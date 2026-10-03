"""
pairwise-football-manager-system - FootballManagerSystem

A football (soccer) manager simulation covering five subsystems:

- Player development: growth, condition (fatigue/injury) and morale.
- Tactics: formations, team instructions and opponent-specific adaptation.
- Transfers: negotiation, contracts and budget control.
- Matches: possession, shots and disciplinary (cards) simulation.
- Youth academy: potential, coaches and facilities.

All state is kept in plain dicts so the system is easy to inspect and test.
"""

import random

DEFAULT_ATTRIBUTES = {
    "pace": 60,
    "shooting": 60,
    "passing": 60,
    "defending": 60,
    "physical": 60,
}

# Formation shape: (defenders, midfielders, forwards)
FORMATIONS = {
    "442": (4, 4, 2),
    "433": (4, 3, 3),
    "352": (3, 5, 2),
    "4231": (4, 3, 1),
    "532": (5, 3, 2),
    "343": (3, 4, 3),
}

# Team instruction presets: how each style shifts the tactical profile.
INSTRUCTIONS = {
    "attacking": {"attack": 0.15, "defense": -0.10, "tempo": 0.10},
    "defensive": {"attack": -0.10, "defense": 0.15, "tempo": -0.10},
    "balanced": {"attack": 0.0, "defense": 0.0, "tempo": 0.0},
    "counter": {"attack": 0.05, "defense": 0.10, "tempo": 0.05},
    "possession": {"attack": 0.05, "defense": 0.05, "tempo": -0.05},
}


def _clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


class FootballManagerSystem:
    def __init__(self, seed=None):
        self.state = {}
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Player development: growth, condition (fatigue/injury) and morale
    # ------------------------------------------------------------------
    def update_player(self, player=None, training_intensity=0.5,
                      match_result=None, injured=False, matches_played=0):
        """Update a player after training/matches.

        Growth: attributes rise with training, scaled by age (young players
        grow faster) and capped by potential.
        Condition: fatigue builds with training/matches and lowers condition;
        injuries hit condition hard.
        Morale: wins lift morale, defeats sink it; low condition drags it too.
        """
        player = dict(player) if player else {}
        player.setdefault("name", "Unknown")
        player.setdefault("age", 20)
        player.setdefault("potential", 80)
        player.setdefault("attributes", dict(DEFAULT_ATTRIBUTES))
        player["attributes"] = {**DEFAULT_ATTRIBUTES, **player["attributes"]}
        player.setdefault("condition", 100.0)
        player.setdefault("morale", 50.0)
        player.setdefault("injured", False)

        training_intensity = _clamp(float(training_intensity), 0.0, 1.0)
        potential = player["potential"]

        # --- Growth: young players improve faster, capped by potential ---
        age_factor = max(0.0, (30.0 - player["age"]) / 20.0)
        growth_rate = training_intensity * age_factor * 2.0
        for attr, value in player["attributes"].items():
            if value < potential:
                headroom = (potential - value) / 100.0
                player["attributes"][attr] = round(
                    min(potential, value + growth_rate * headroom), 2)

        # --- Condition: fatigue from training and matches, injuries hurt ---
        fatigue = training_intensity * 10.0 + matches_played * 5.0
        condition = player["condition"] - fatigue
        if injured:
            condition -= 30.0
            player["injured"] = True
        else:
            player["injured"] = False
            condition += 5.0  # natural recovery when healthy
        player["condition"] = round(_clamp(condition), 2)

        # --- Morale: results and fitness move morale up or down ---
        morale = player["morale"]
        if match_result == "win":
            morale += 10.0
        elif match_result == "loss":
            morale -= 10.0
        elif match_result == "draw":
            morale += 2.0
        if player["injured"]:
            morale -= 5.0
        if player["condition"] < 50.0:
            morale -= 3.0
        player["morale"] = round(_clamp(morale), 2)

        return player

    # ------------------------------------------------------------------
    # Tactics: formation, instructions and opponent adaptation
    # ------------------------------------------------------------------
    def apply_tactic(self, formation="433", instructions="balanced",
                     opponent=None):
        """Build a tactical setup.

        Formation: sets the defensive/midfield/attacking shape.
        Instructions: attacking/defensive/etc. shift the team profile.
        Adaptation: the plan is adjusted to counter the opponent's style.
        """
        formation = str(formation).replace("-", "")
        if formation not in FORMATIONS:
            raise ValueError(f"unknown formation: {formation!r}")
        if instructions not in INSTRUCTIONS:
            raise ValueError(f"unknown instructions: {instructions!r}")

        defenders, midfielders, forwards = FORMATIONS[formation]

        # Base profile derived from the formation shape.
        attack = 0.30 + forwards * 0.10
        defense = 0.30 + defenders * 0.10
        possession = 0.30 + midfielders * 0.05

        # Team instructions modify the profile.
        mod = INSTRUCTIONS[instructions]
        attack += mod["attack"]
        defense += mod["defense"]
        possession += mod["tempo"] / 2.0

        # Adapt to the opponent: counter their strengths, target weaknesses.
        adaptations = []
        if opponent:
            style = opponent.get("style")
            strength = opponent.get("strength", "balanced")
            if style == "attacking" or strength == "attack":
                defense += 0.10
                attack -= 0.05
                adaptations.append("sit deeper to absorb their attack")
            elif style == "defensive" or strength == "defense":
                attack += 0.10
                possession += 0.05
                adaptations.append("commit more men forward to break them down")
            elif style == "possession":
                possession -= 0.05
                attack += 0.05
                adaptations.append("press high to disrupt their passing")
            if opponent.get("weakness") == "defense":
                attack += 0.05
                adaptations.append("exploit their weak defense")

        profile = {
            "attack": round(_clamp(attack, 0.0, 1.0), 3),
            "defense": round(_clamp(defense, 0.0, 1.0), 3),
            "possession": round(_clamp(possession, 0.0, 1.0), 3),
        }
        return {
            "formation": formation,
            "shape": {"defenders": defenders, "midfielders": midfielders,
                      "forwards": forwards},
            "instructions": instructions,
            "profile": profile,
            "adaptations": adaptations,
        }

    # ------------------------------------------------------------------
    # Transfers: negotiation, contract and budget
    # ------------------------------------------------------------------
    def transfer_player(self, player=None, offer=None, budget=None,
                        asking_price=None, selling_club=None,
                        contract_years=3, wage=None, max_rounds=3):
        """Attempt to sign a player.

        Negotiation: offers below the asking price are rejected; the selling
        club counters and the buyer may improve the bid over several rounds.
        Budget: a deal can never exceed the available budget.
        Contract: a completed transfer always produces a signed contract.
        """
        player = dict(player) if player else {"name": "Unknown"}
        value = float(player.get("value", 10_000_000))
        asking = float(asking_price) if asking_price is not None else value
        budget = float(budget) if budget is not None else asking
        offer = float(offer) if offer is not None else asking
        wage = float(wage) if wage is not None else value / 50.0
        club = selling_club or player.get("club", "selling_club")

        history = []
        accepted = False
        fee = None

        for _round in range(1, max_rounds + 1):
            if offer > budget:
                history.append({"round": _round, "offer": offer,
                                "status": "rejected",
                                "reason": "offer exceeds budget"})
                return {"success": False, "player": player["name"],
                        "reason": "insufficient budget", "history": history,
                        "contract": None}
            if offer >= asking:
                accepted = True
                fee = offer
                history.append({"round": _round, "offer": offer,
                                "status": "accepted"})
                break
            # Rejected: the club counters halfway to the asking price.
            counter = (offer + asking) / 2.0
            history.append({"round": _round, "offer": offer,
                            "status": "rejected", "counter": counter})
            offer = min(counter * 1.05, budget)

        if not accepted:
            return {"success": False, "player": player["name"],
                    "reason": "negotiation broke down", "history": history,
                    "contract": None}

        # A completed transfer always includes a signed contract.
        contract = {
            "player": player["name"],
            "from": club,
            "fee": fee,
            "years": contract_years,
            "wage_per_week": round(wage, 2),
            "signed": True,
        }
        return {"success": True, "player": player["name"], "fee": fee,
                "budget_remaining": round(budget - fee, 2),
                "history": history, "contract": contract}

    # ------------------------------------------------------------------
    # Matches: possession, shots and discipline (cards)
    # ------------------------------------------------------------------
    def simulate_match(self, home_team=None, away_team=None, seed=None):
        """Simulate a match between two teams.

        Possession: derived from each team's midfield strength (never a
        fixed 50:50). Shots: flow from attack strength and possession, and
        goals come from shots. Discipline: fouls are judged and can produce
        yellow and red cards.
        """
        rng = random.Random(seed) if seed is not None else self._rng
        home = {"name": "Home", "attack": 70, "midfield": 70,
                "defense": 70, "aggression": 0.5}
        away = {"name": "Away", "attack": 70, "midfield": 70,
                "defense": 70, "aggression": 0.5}
        if home_team:
            home.update(home_team)
        if away_team:
            away.update(away_team)

        # --- Possession from midfield strength ---
        total_mid = home["midfield"] + away["midfield"]
        home_possession = home["midfield"] / total_mid if total_mid else 0.5
        home_possession += rng.uniform(-0.03, 0.03)
        home_possession = _clamp(home_possession, 0.2, 0.8)

        def play_side(attack, defense, possession, aggression, name):
            # --- Shots: attack strength + possession drive shot volume ---
            shots = max(0, round(
                (attack / 10.0) * (0.5 + possession)
                - (defense / 40.0) + rng.uniform(-1.5, 1.5)))
            on_target = sum(1 for _ in range(shots)
                            if rng.random() < attack / (attack + defense))
            # --- Goals come from shots on target ---
            goals = sum(1 for _ in range(on_target)
                        if rng.random() < 0.3 * attack / 70.0)
            # --- Discipline: fouls are judged, cards are handed out ---
            fouls = max(0, round(aggression * 12 + rng.uniform(-2, 4)))
            yellow = sum(1 for _ in range(fouls) if rng.random() < 0.25)
            red = 1 if yellow >= 3 and rng.random() < 0.5 else 0
            yellow = min(yellow, 2) if red else yellow
            return {"name": name, "shots": shots, "shots_on_target": on_target,
                    "goals": goals, "fouls": fouls,
                    "yellow_cards": yellow, "red_cards": red}

        home_stats = play_side(home["attack"], away["defense"],
                               home_possession, home["aggression"],
                               home["name"])
        away_stats = play_side(away["attack"], home["defense"],
                               1.0 - home_possession, away["aggression"],
                               away["name"])

        return {
            "home": home_stats,
            "away": away_stats,
            "score": (home_stats["goals"], away_stats["goals"]),
            "possession": {"home": round(home_possession * 100, 1),
                           "away": round((1.0 - home_possession) * 100, 1)},
        }

    # ------------------------------------------------------------------
    # Youth academy: potential, coaches and facilities
    # ------------------------------------------------------------------
    def train_youth(self, player=None, coach_quality=0.5,
                    facility_level=1, sessions=1):
        """Train a youth player.

        Potential: each prospect has their own potential cap, so growth
        ceilings differ per player.
        Coaches: better coaches (coach_quality 0..1) accelerate growth.
        Facilities: higher facility_level (1..5) further boosts growth.
        """
        player = dict(player) if player else {}
        player.setdefault("name", "Youth Prospect")
        player.setdefault("age", 16)
        player.setdefault("potential", 75)
        player.setdefault("attributes", dict(DEFAULT_ATTRIBUTES))
        player["attributes"] = {**DEFAULT_ATTRIBUTES, **player["attributes"]}

        coach_quality = _clamp(float(coach_quality), 0.0, 1.0)
        facility_level = int(_clamp(facility_level, 1, 5))
        sessions = max(1, int(sessions))

        coach_multiplier = 0.5 + coach_quality * 1.5
        facility_multiplier = 0.8 + (facility_level - 1) * 0.15
        potential = player["potential"]

        total_growth = 0.0
        for _ in range(sessions):
            for attr, value in player["attributes"].items():
                if value >= potential:
                    continue
                headroom = (potential - value) / 100.0
                gain = headroom * coach_multiplier * facility_multiplier
                player["attributes"][attr] = round(
                    min(potential, value + gain), 2)
                total_growth += gain

        return {
            "player": player,
            "potential": potential,
            "coach_quality": coach_quality,
            "facility_level": facility_level,
            "sessions": sessions,
            "growth": round(total_growth, 2),
        }
