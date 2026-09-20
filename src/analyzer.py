import re
from typing import List, Dict
from pydantic import BaseModel

class RosterPlayer(BaseModel):
    slot: str
    name: str
    team: str
    status: str
    proj_pts: float

class LeagueRosterState(BaseModel):
    league_name: str
    faab_remaining: int
    starters: List[RosterPlayer] = []
    bench: List[RosterPlayer] = []

def parse_league_roster(markdown_text: str, league_name: str) -> LeagueRosterState:
    """Extracts active starters and bench players across line endings and formats."""
    faab = 100
    faab_match = re.search(r"FAAB Remaining:\s*\$(\d+)", markdown_text, re.IGNORECASE)
    if faab_match:
        faab = int(faab_match.group(1))

    starters = []
    bench = []

    current_section = None
    lines = markdown_text.replace("\r\n", "\n").split("\n")

    for line in lines:
        stripped = line.strip()

        # Header section tracking
        if "### Starters" in stripped or "## Starters" in stripped:
            current_section = "starters"
            continue
        elif "### Bench" in stripped or "## Bench" in stripped:
            current_section = "bench"
            continue
        elif stripped.startswith("###") or stripped.startswith("##") or stripped.startswith("---"):
            current_section = None
            continue

        # Parse Starters
        if current_section == "starters":
            m = re.search(r"-\s*\*\*(.*?):\*\*\s*([^(]+)\(([A-Z0-9]{2,4})\)", stripped)
            if m:
                slot = m.group(1).strip()
                name = m.group(2).strip()
                team = m.group(3).strip()
                p_match = re.search(r"Proj:\s*([\d\.]+)", stripped)
                proj = float(p_match.group(1)) if p_match else 0.0
                
                starters.append(RosterPlayer(
                    slot=slot, name=name, team=team,
                    status="[ACTIVE]", proj_pts=proj
                ))

        # Parse Bench
        elif current_section == "bench":
            m = re.search(r"-\s*BN\s*\(([^)]+)\):\s*([^(]+)\(([A-Z0-9]{2,4})\)", stripped)
            if m:
                slot = m.group(1).strip()
                name = m.group(2).strip()
                team = m.group(3).strip()
                p_match = re.search(r"Proj:\s*([\d\.]+)", stripped)
                proj = float(p_match.group(1)) if p_match else 0.0
                
                bench.append(RosterPlayer(
                    slot=slot, name=name, team=team,
                    status="[ACTIVE]", proj_pts=proj
                ))

    return LeagueRosterState(
        league_name=league_name,
        faab_remaining=faab,
        starters=starters,
        bench=bench
    )

def generate_waiver_recommendations(snapshot_parsed, roster: LeagueRosterState) -> Dict:
    """Pairs top waiver targets against lowest-projected bench players."""
    
    # Sort bench ascending by projected points to find drop candidates
    drop_candidates = sorted(roster.bench, key=lambda p: p.proj_pts)
    
    eligible_targets = [
        t for t in snapshot_parsed.top_waiver_targets 
        if "Tier 1" in t.priority_tier or "Tier 2" in t.priority_tier
    ]

    recommendations = []
    for idx, target in enumerate(eligible_targets[:3]):
        if idx < len(drop_candidates):
            drop_player = f"{drop_candidates[idx].name} ({drop_candidates[idx].slot}, {drop_candidates[idx].proj_pts} pts)"
        else:
            drop_player = "Open Bench Slot"
            
        suggested_bid = 3 if "Tier 1" in target.priority_tier else 1
        
        recommendations.append({
            "add": f"{target.player} ({target.pos}, {target.team})",
            "drop": drop_player,
            "tier": target.priority_tier,
            "proj_pts": target.proj_pts,
            "suggested_bid": f"${suggested_bid}"
        })

    return {
        "league": roster.league_name,
        "faab_available": f"${roster.faab_remaining}",
        "recommendations": recommendations
    }
