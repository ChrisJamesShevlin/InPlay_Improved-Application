import tkinter as tk
from tkinter import ttk
from math import exp, factorial

class FootballBettingModel:
    def __init__(self, root):
        self.root = root
        self.root.title("Football Betting Model")
        self.create_widgets()
        self.previous_values = {}

    def create_widgets(self):
        self.fields = {
            "Home Avg Goals Scored": tk.DoubleVar(),
            "Home Avg Goals Conceded": tk.DoubleVar(),
            "Away Avg Goals Scored": tk.DoubleVar(),
            "Away Avg Goals Conceded": tk.DoubleVar(),
            "Home Xg": tk.DoubleVar(),
            "Away Xg": tk.DoubleVar(),
            "Elapsed Minutes": tk.DoubleVar(),
            "Home Goals": tk.IntVar(),
            "Away Goals": tk.IntVar(),
            "In-Game Home Xg": tk.DoubleVar(),
            "In-Game Away Xg": tk.DoubleVar(),
            "Home Possession %": tk.DoubleVar(),
            "Away Possession %": tk.DoubleVar(),
            "Home Shots on Target": tk.IntVar(),  # New field
            "Away Shots on Target": tk.IntVar(),  # New field
            "Account Balance": tk.DoubleVar(),
            "Live Home Odds": tk.DoubleVar(),
            "Live Away Odds": tk.DoubleVar(),
            "Live Draw Odds": tk.DoubleVar()
        }

        row = 0
        for field, var in self.fields.items():
            label = ttk.Label(self.root, text=field)
            label.grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
            entry = ttk.Entry(self.root, textvariable=var)
            entry.grid(row=row, column=1, padx=5, pady=5)
            row += 1

        calculate_button = ttk.Button(self.root, text="Calculate", command=self.calculate_fair_odds)
        calculate_button.grid(row=row, column=0, columnspan=2, pady=10)
        
        reset_button = ttk.Button(self.root, text="Reset Fields", command=self.reset_fields)
        reset_button.grid(row=row+1, column=0, columnspan=2, pady=10)

        self.result_label = ttk.Label(self.root, text="")
        self.result_label.grid(row=row+2, column=0, columnspan=2, pady=10)

    def reset_fields(self):
        for var in self.fields.values():
            if isinstance(var, tk.DoubleVar):
                var.set(0.0)
            elif isinstance(var, tk.IntVar):
                var.set(0)
        self.previous_values.clear()

    def zero_inflated_poisson_probability(self, lam, k, p_zero=0.06):
        if k == 0:
            return p_zero + (1 - p_zero) * exp(-lam)
        return (1 - p_zero) * ((lam ** k) * exp(-lam)) / factorial(k)

    def time_decay_adjustment(self, lambda_xg, elapsed_minutes):
        decay_factor = max(0.5, 1 - (elapsed_minutes / 90))
        return lambda_xg * decay_factor

    def dynamic_kelly(self, edge, odds):
        if odds >= 20.0:
            return 0  # Avoid extreme odds
        
        if odds > 1.0:
            # Scale the fraction based on the size of the edge
            fraction = 0.18 if odds < 2.0 else 0.12 if odds < 8.0 else 0.06
            scaled_fraction = fraction * (edge / (odds - 1))
            return max(0, scaled_fraction)
        
        return 0

    def calculate_fair_odds(self):
        home_xg = self.fields["Home Xg"].get()
        away_xg = self.fields["Away Xg"].get()
        elapsed_minutes = self.fields["Elapsed Minutes"].get()
        home_goals = self.fields["Home Goals"].get()
        away_goals = self.fields["Away Goals"].get()
        in_game_home_xg = self.fields["In-Game Home Xg"].get()
        in_game_away_xg = self.fields["In-Game Away Xg"].get()
        home_possession = self.fields["Home Possession %"].get()
        away_possession = self.fields["Away Possession %"].get()
        account_balance = self.fields["Account Balance"].get()
        live_home_odds = self.fields["Live Home Odds"].get()
        live_away_odds = self.fields["Live Away Odds"].get()
        live_draw_odds = self.fields["Live Draw Odds"].get()

        home_avg_goals_scored = self.fields["Home Avg Goals Scored"].get()
        home_avg_goals_conceded = self.fields["Home Avg Goals Conceded"].get()
        away_avg_goals_scored = self.fields["Away Avg Goals Scored"].get()
        away_avg_goals_conceded = self.fields["Away Avg Goals Conceded"].get()

        home_sot = self.fields["Home Shots on Target"].get()  # New field
        away_sot = self.fields["Away Shots on Target"].get()  # New field

        if self.previous_values:
            previous_in_game_home_xg = self.previous_values.get("In-Game Home Xg", in_game_home_xg)
            previous_in_game_away_xg = self.previous_values.get("In-Game Away Xg", in_game_away_xg)
            previous_home_possession = self.previous_values.get("Home Possession %", home_possession)
            previous_away_possession = self.previous_values.get("Away Possession %", away_possession)

            home_xg_change = in_game_home_xg - previous_in_game_home_xg
            away_xg_change = in_game_away_xg - previous_in_game_away_xg
            home_possession_change = home_possession - previous_home_possession
            away_possession_change = away_possession - previous_away_possession

            in_game_home_xg = previous_in_game_home_xg + home_xg_change
            in_game_away_xg = previous_in_game_away_xg + away_xg_change
            home_possession = previous_home_possession + home_possession_change
            away_possession = previous_away_possession + away_possession_change

        self.previous_values = {
            "In-Game Home Xg": in_game_home_xg,
            "In-Game Away Xg": in_game_away_xg,
            "Home Possession %": home_possession,
            "Away Possession %": away_possession
        }

        remaining_minutes = 90 - elapsed_minutes
        lambda_home = self.time_decay_adjustment(in_game_home_xg + (home_xg * remaining_minutes / 90), elapsed_minutes)
        lambda_away = self.time_decay_adjustment(in_game_away_xg + (away_xg * remaining_minutes / 90), elapsed_minutes)

        lambda_home = (lambda_home * 0.85) + ((home_avg_goals_scored / max(0.75, away_avg_goals_conceded)) * 0.15)
        lambda_away = (lambda_away * 0.85) + ((away_avg_goals_scored / max(0.75, home_avg_goals_conceded)) * 0.15)

        lambda_home *= 1 + ((home_possession - 50) / 200)
        lambda_away *= 1 + ((away_possession - 50) / 200)

        home_win_probability, away_win_probability, draw_probability = 0, 0, 0

        for home_goals_remaining in range(6):
            for away_goals_remaining in range(6):
                prob = self.zero_inflated_poisson_probability(lambda_home, home_goals_remaining) * \
                       self.zero_inflated_poisson_probability(lambda_away, away_goals_remaining)

                if home_goals + home_goals_remaining > away_goals + away_goals_remaining:
                    home_win_probability += prob
                elif home_goals + home_goals_remaining < away_goals + away_goals_remaining:
                    away_win_probability += prob
                else:
                    draw_probability += prob

        total_prob = home_win_probability + away_win_probability + draw_probability
        if total_prob > 0:
            home_win_probability /= total_prob
            away_win_probability /= total_prob
            draw_probability /= total_prob

        fair_home_odds = 1 / home_win_probability
        fair_away_odds = 1 / away_win_probability
        fair_draw_odds = 1 / draw_probability

        # Weighted calculation of which team is more likely to score next
        home_contribution = (lambda_home * 0.4) + (in_game_home_xg * 0.3) + (home_sot * 0.2) + (home_goals * 0.1)
        away_contribution = (lambda_away * 0.4) + (in_game_away_xg * 0.3) + (away_sot * 0.2) + (away_goals * 0.1)

        if home_contribution > away_contribution:
            goal_source = "Home"
            lambda_home -= 0.04  # Bias toward stronger team
        elif away_contribution > home_contribution:
            goal_source = "Away"
            lambda_away += 0.04  # More variance for weaker team
        else:
            goal_source = "Even"

        lay_opportunities = []
        max_edge = 0  # Track the highest edge

        results = "Fair Odds & Edge:\n"

        for outcome, fair_odds, live_odds in [("Home", fair_home_odds, live_home_odds),
                                              ("Away", fair_away_odds, live_away_odds),
                                              ("Draw", fair_draw_odds, live_draw_odds)]:
            edge = (fair_odds - live_odds) / fair_odds if live_odds < fair_odds else 0.0000
            results += f"{outcome}: Fair {fair_odds:.2f} | Edge {edge:.4f}\n"
            
            if live_odds < fair_odds and live_odds < 20 and edge > 0:
                kelly_fraction = self.dynamic_kelly(edge, live_odds)
                stake = account_balance * kelly_fraction
                liability = stake * (live_odds - 1)

                lay_opportunities.append((edge, outcome, live_odds, stake, liability))

                if edge > max_edge:
                    max_edge = edge  # Track the highest edge

        if lay_opportunities:
            results += "\nLaying Opportunities:\n"
            for edge, outcome, live_odds, stake, liability in sorted(lay_opportunities, reverse=True):
                color = "green"  # Default to green for small edges
                if edge == max_edge:
                    color = "red"  # Highlight the best edge in red
                elif edge > 0.03:  # Medium edge
                    color = "orange"

                results += f"\n🟢 Lay {outcome} at {live_odds:.2f} | Edge: {edge:.4f} | Stake: {stake:.2f} | Liability: {liability:.2f}" \
                    if color == "green" else \
                    f"\n🟠 Lay {outcome} at {live_odds:.2f} | Edge: {edge:.4f} | Stake: {stake:.2f} | Liability: {liability:.2f}" \
                    if color == "orange" else \
                    f"\n🔴 Lay {outcome} at {live_odds:.2f} | Edge: {edge:.4f} | Stake: {stake:.2f} | Liability: {liability:.2f}"
        else:
            results += "\nNo value lay bets found."

        results += f"\nGoal Probability: {home_win_probability + away_win_probability:.2%} ({goal_source})\n"
        self.result_label.config(text=results)

if __name__ == "__main__":
    root = tk.Tk()
    app = FootballBettingModel(root)
    root.mainloop()
