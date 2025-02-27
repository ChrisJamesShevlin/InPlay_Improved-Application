import tkinter as tk
from tkinter import ttk
from math import exp, factorial

class FootballBettingModel:
    def __init__(self, root):
        self.root = root
        self.root.title("Football Betting Model")
        self.create_widgets()
        self.history = {
            "home_xg": [],
            "away_xg": [],
            "home_sot": [],
            "away_sot": [],
            "home_possession": [],
            "away_possession": []
        }
        self.history_length = 10  # Store last 10 updates

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
        self.history = {
            "home_xg": [],
            "away_xg": [],
            "home_sot": [],
            "away_sot": [],
            "home_possession": [],
            "away_possession": []
        }

    def zero_inflated_poisson_probability(self, lam, k, p_zero=0.06):
        if k == 0:
            return p_zero + (1 - p_zero) * exp(-lam)
        return (1 - p_zero) * ((lam ** k) * exp(-lam)) / factorial(k)

    def time_decay_adjustment(self, lambda_xg, elapsed_minutes):
        decay_factor = max(0.5, 1 - (elapsed_minutes / 90))
        return lambda_xg * decay_factor

    def dynamic_kelly(self, edge):
        # Fixed 12% Kelly criterion regardless of odds
        kelly_fraction = 0.12 * edge
        return max(0, kelly_fraction)

    def update_history(self, key, value):
        """Store the last 10 values of a given key."""
        if len(self.history[key]) >= self.history_length:
            self.history[key].pop(0)  # Remove oldest entry
        self.history[key].append(value)

    def get_recent_trend(self, key):
        """Get the recent change over last 3 entries."""
        if len(self.history[key]) < 3:
            return 0  # Not enough data
        return self.history[key][-1] - self.history[key][-3]  # Change over last 3 updates

    def detect_momentum_peak(self):
        """Detects if a team is at peak momentum but the market hasn't adjusted yet."""
        trend_home_xg = self.get_recent_trend("home_xg")
        trend_away_xg = self.get_recent_trend("away_xg")
        trend_home_sot = self.get_recent_trend("home_sot")
        trend_away_sot = self.get_recent_trend("away_sot")

        if trend_home_xg > 0.3 and trend_home_sot > 1:
            return "📈 Home team at peak momentum! Possible lay bet on Away before odds adjust."
        elif trend_away_xg > 0.3 and trend_away_sot > 1:
            return "📉 Away team at peak momentum! Possible lay bet on Home before odds adjust."

        return None  # No peak detected

    def detect_market_overreaction(self, fair_home_odds, live_home_odds, fair_away_odds, live_away_odds, fair_draw_odds, live_draw_odds):
        """Identifies when live odds overreact, creating a value lay opportunity."""
        signals = []
        
        if live_home_odds > fair_home_odds * 1.15:
            signals.append("⚠️ Market overreaction on Home odds!")
        if live_away_odds > fair_away_odds * 1.15:
            signals.append("⚠️ Market overreaction on Away odds!")
        if live_draw_odds > fair_draw_odds * 1.15:
            signals.append("⚠️ Market overreaction on Draw odds!")

        return "\n".join(signals) if signals else None

    def detect_reversal_point(self):
        """Detects when a previously dominant team starts fading."""
        trend_home_xg = self.get_recent_trend("home_xg")
        trend_away_xg = self.get_recent_trend("away_xg")
        trend_home_sot = self.get_recent_trend("home_sot")
        trend_away_sot = self.get_recent_trend("away_sot")
        trend_home_possession = self.get_recent_trend("home_possession")
        trend_away_possession = self.get_recent_trend("away_possession")

        if trend_home_xg < 0 and trend_home_sot < 0 and trend_away_possession > 3:
            return "🔄 Home team losing momentum! Possible lay bet on Home."
        elif trend_away_xg < 0 and trend_away_sot < 0 and trend_home_possession > 3:
            return "🔄 Away team losing momentum! Possible lay bet on Away."

        return None

    def optimal_betting_window(self, elapsed_minutes):
        """Suggests best match phase to place lay bets based on in-game trends."""
        if elapsed_minutes < 30:
            return "⚠️ Early Game: High volatility. Only bet if extreme value."
        elif 30 <= elapsed_minutes < 45:
            return "🔍 30-45 min: Watching trends. Lay if strong edge detected."
        elif 45 <= elapsed_minutes < 60:
            return "🛠 45-60 min: Tactical shifts. Lay if favorite struggles."
        elif 60 <= elapsed_minutes < 75:
            return "🔥 Prime Betting Window (60-75 min). Strong lay opportunities!"
        elif elapsed_minutes >= 75:
            return "⚠️ Late Game: Market tightening. Higher risk on lays."

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

        self.update_history("home_xg", home_xg)
        self.update_history("away_xg", away_xg)
        self.update_history("home_sot", home_sot)
        self.update_history("away_sot", away_sot)
        self.update_history("home_possession", home_possession)
        self.update_history("away_possession", away_possession)

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

        lay_opportunity = None
        max_edge = 0  # Track the highest edge

        results = "Fair Odds & Edge:\n"

        for outcome, fair_odds, live_odds in [("Home", fair_home_odds, live_home_odds),
                                              ("Away", fair_away_odds, live_away_odds),
                                              ("Draw", fair_draw_odds, live_draw_odds)]:
            edge = (fair_odds - live_odds) / fair_odds if live_odds < fair_odds else 0.0000
            results += f"{outcome}: Fair {fair_odds:.2f} | Edge {edge:.4f}\n"
            
            if live_odds < fair_odds and live_odds < 20 and edge > max_edge:
                kelly_fraction = self.dynamic_kelly(edge)
                liability = account_balance * kelly_fraction
                stake = liability / (live_odds - 1)

                lay_opportunity = (edge, outcome, live_odds, stake, liability)
                max_edge = edge  # Track the highest edge

        if lay_opportunity:
            edge, outcome, live_odds, stake, liability = lay_opportunity

            # Give confidence level based on timing
            if elapsed_minutes >= 60 and elapsed_minutes < 75:
                results += f"\n🔴 Lay {outcome} at {live_odds:.2f} | Edge: {edge:.4f} | Stake: {stake:.2f} | Liability: {liability:.2f} ✅ Best Timing!"
            elif elapsed_minutes >= 75:
                results += f"\n🔴 Lay {outcome} at {live_odds:.2f} | Edge: {edge:.4f} | Stake: {stake:.2f} | Liability: {liability:.2f} ⚠️ Late-game risk!"
            elif elapsed_minutes < 30:
                results += f"\n🔴 Lay {outcome} at {live_odds:.2f} | Edge: {edge:.4f} | Stake: {stake:.2f} | Liability: {liability:.2f} ⚠️ High volatility!"
            else:
                results += f"\n🔴 Lay {outcome} at {live_odds:.2f} | Edge: {edge:.4f} | Stake: {stake:.2f} | Liability: {liability:.2f} 🚦 Mid-game adjustment."
        else:
            results += "\nNo value lay bets found."

        trend_home_xg = self.get_recent_trend("home_xg")
        trend_away_xg = self.get_recent_trend("away_xg")
        trend_home_sot = self.get_recent_trend("home_sot")
        trend_away_sot = self.get_recent_trend("away_sot")
        trend_home_possession = self.get_recent_trend("home_possession")
        trend_away_possession = self.get_recent_trend("away_possession")

        # If a team is gaining momentum, adjust fair odds weight slightly
        if trend_home_xg > 0.2 or trend_home_sot > 1 or trend_home_possession > 3:
            results += "\n📈 Home team gaining momentum! Consider value bet.\n"
        elif trend_away_xg > 0.2 or trend_away_sot > 1 or trend_away_possession > 3:
            results += "\n📉 Away team gaining momentum! Consider value bet.\n"

        results += f"\nGoal Probability: {home_win_probability + away_win_probability:.2%} ({goal_source})\n"

        # Detect momentum trends
        momentum_signal = self.detect_momentum_peak()
        reversal_signal = self.detect_reversal_point()
        betting_window_signal = self.optimal_betting_window(elapsed_minutes)

        # Detect market overreaction (for signals only)
        overreaction_signal = self.detect_market_overreaction(fair_home_odds, live_home_odds, fair_away_odds, live_away_odds, fair_draw_odds, live_draw_odds)

        # Combine all signals
        betting_signals = "\n📊 Betting Insights:\n"
        if momentum_signal:
            betting_signals += f"{momentum_signal}\n"
        if reversal_signal:
            betting_signals += f"{reversal_signal}\n"
        if betting_window_signal:
            betting_signals += f"{betting_window_signal}\n"
        if overreaction_signal:
            betting_signals += f"{overreaction_signal}\n"

        # Update UI or print signals
        self.result_label.config(text=results + betting_signals)

if __name__ == "__main__":
    root = tk.Tk()
    app = FootballBettingModel(root)
    root.mainloop()
