from src.fetcher import fetch_all
from src.parser import parse_snapshot
from src.analyzer import parse_league_roster, generate_waiver_recommendations

def main():
    print("🤖 FANTASY AI AGENT ENGINE (LOCAL)")
    print("====================================")
    
    # 1. Fetch live documents
    docs = fetch_all()
    
    # 2. Parse telemetry snapshot
    snapshot_parsed = parse_snapshot(docs["snapshot"])
    
    # 3. Parse user rosters
    hathat_roster = parse_league_roster(docs["hathat"], "Hat Hat Loop")
    bush_roster = parse_league_roster(docs["bush"], "Bush League")
    
    print("\n====================================")
    print("📊 LEAGUE TELEMETRY OVERVIEW")
    print("====================================")
    print(f"Timestamp: {snapshot_parsed.last_updated}")
    print(f"Week {snapshot_parsed.week}, Season {snapshot_parsed.season}")
    print(f"• Hat Hat Loop FAAB: ${hathat_roster.faab_remaining} (Parsed {len(hathat_roster.bench)} Bench Players)")
    print(f"• Bush League FAAB:   ${bush_roster.faab_remaining} (Parsed {len(bush_roster.bench)} Bench Players)")

    # 4. Generate Recommendations for both leagues
    for roster in [hathat_roster, bush_roster]:
        rec_data = generate_waiver_recommendations(snapshot_parsed, roster)
        
        print("\n====================================")
        print(f"🎯 RECOMMENDED WAIVER ACTIONS ({rec_data['league']})")
        print("====================================")
        
        for idx, rec in enumerate(rec_data["recommendations"], 1):
            print(f"\n{idx}. ADD: {rec['add']} [{rec['tier']}]")
            print(f"   • Suggested Drop: {rec['drop']}")
            print(f"   • Recommended FAAB Bid: {rec['suggested_bid']}")
            print(f"   • Target Projection: {rec['proj_pts']} pts")

if __name__ == "__main__":
    main()
