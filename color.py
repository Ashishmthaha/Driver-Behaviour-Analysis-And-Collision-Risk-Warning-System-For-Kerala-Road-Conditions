# ============================================================================
#  SUMO VEHICLE RISK COLORING - COLLISION WARNINGS + CSV PREDICTIONS
#  RED = SUMO Collision Warning OR High Risk (CSV)
#  GREEN = Medium Risk (CSV)
#  BLUE = Low Risk (CSV)
# ============================================================================
import traci
import pandas as pd
import os
import sys

# ============================================================================
# CONFIGURATION
# ============================================================================
SUMO_CFG = "test.sumocfg"
PREDICTION_CSV = "kulathara_traffic_features_TEST_v6 (1)_WITH_PREDICTIONS.csv"

# Risk colors in RGBA (0-255 range for SUMO)
# Format: (Red, Green, Blue, Alpha)
RISK_COLORS = {
    'high':   (255, 0, 0, 255),      # 🔴 RED - High Risk OR Collision Warning
    'medium': (0, 255, 0, 255),      # 🟢 GREEN - Medium Risk
    'low':    (0, 0, 255, 255)       # 🔵 BLUE - Low Risk
}

# ============================================================================
# LOAD PREDICTIONS
# ============================================================================
print("="*70)
print(" SUMO VEHICLE COLORING - COLLISION WARNINGS + CSV PREDICTIONS")
print("="*70)

print(f"\n📁 Loading predictions from: {PREDICTION_CSV}")
if not os.path.exists(PREDICTION_CSV):
    print(f"❌ Error: File not found: {PREDICTION_CSV}")
    print(f"   Current directory: {os.getcwd()}")
    sys.exit(1)

df_pred = pd.read_csv(PREDICTION_CSV)
print(f"✅ Loaded {len(df_pred):,} prediction records")

# Check for required columns
required_cols = ['vehicle_id', 'timestamp', 'predicted_risk']
missing_cols = [col for col in required_cols if col not in df_pred.columns]
if missing_cols:
    print(f"❌ Error: Missing columns: {missing_cols}")
    print(f"   Available columns: {df_pred.columns.tolist()}")
    sys.exit(1)

# Create lookup: (vehicle_id, timestamp) -> risk level
vehicle_risk_by_time = df_pred.set_index(['vehicle_id', 'timestamp'])['predicted_risk'].to_dict()

# Count risk distribution
risk_counts = df_pred['predicted_risk'].value_counts()
print(f"\n📊 CSV Risk Distribution:")
print(f"   🔴 High Risk:   {risk_counts.get('high', 0):,} records")
print(f"   🟢 Medium Risk: {risk_counts.get('medium', 0):,} records")
print(f"   🔵 Low Risk:    {risk_counts.get('low', 0):,} records")

# Get unique vehicles
unique_vehicles = df_pred['vehicle_id'].nunique()
print(f"\n🚗 Total unique vehicles: {unique_vehicles:,}")

# ============================================================================
# START SUMO GUI
# ============================================================================
print(f"\n🚦 Starting SUMO with config: {SUMO_CFG}")
if not os.path.exists(SUMO_CFG):
    print(f"❌ Error: File not found: {SUMO_CFG}")
    print(f"   Current directory: {os.getcwd()}")
    sys.exit(1)

# Start SUMO GUI with TraCI
try:
    traci.start(["sumo-gui", "-c", SUMO_CFG, "--start", "--quit-on-end"])
    print("✅ SUMO GUI started successfully!")
except Exception as e:
    print(f"❌ Error starting SUMO: {e}")
    print("   Make sure SUMO is installed and added to PATH")
    sys.exit(1)

# ============================================================================
# SIMULATION LOOP
# ============================================================================
step = 0
color_updates = 0
collision_warnings = 0
high_risk_moments = 0

print("\n🎨 Coloring vehicles by risk level...")
print("   🔴 RED   = SUMO Collision Warning OR High Risk (CSV)")
print("   🟢 GREEN = Medium Risk (CSV)")
print("   🔵 BLUE  = Low Risk (CSV)")
print("\n⏱️  Simulation running... (Close GUI window to stop)\n")

try:
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        
        # Get current simulation time (rounded to match CSV timestamps)
        current_time = round(traci.simulation.getTime())
        
        # Get all active vehicles
        vehicle_ids = traci.vehicle.getIDList()
        
        for veh_id in vehicle_ids:
            # Default color based on CSV prediction
            risk_level = vehicle_risk_by_time.get((veh_id, current_time), 'low')
            color = RISK_COLORS.get(risk_level, (0, 0, 255, 255))  # Default blue
            
            # Check for SUMO collision warning
            # Get vehicle's speed and acceleration
            speed = traci.vehicle.getSpeed(veh_id)
            accel = traci.vehicle.getAcceleration(veh_id)
            
            # Check for emergency deceleration (potential collision)
            if accel < -4.0:  # Hard braking (m/s²)
                color = RISK_COLORS['high']  # Force RED
                collision_warnings += 1
            
            # Check for very low gap (using leader vehicle)
            leader = traci.vehicle.getLeader(veh_id, dist=10)  # Check 10m ahead
            if leader:
                leader_id, gap = leader
                if gap < 2.0:  # Very close gap (meters)
                    color = RISK_COLORS['high']  # Force RED
                    collision_warnings += 1
            
            # Check if CSV predicts high risk
            if risk_level == 'high':
                color = RISK_COLORS['high']  # RED
                high_risk_moments += 1
            
            # Apply color to vehicle
            traci.vehicle.setColor(veh_id, color)
            color_updates += 1
        
        step += 1
        
        # Progress indicator every 100 steps
        if step % 100 == 0:
            print(f"   Step {step}: {len(vehicle_ids)} vehicles, "
                  f"{collision_warnings} collision warnings, "
                  f"{high_risk_moments} high-risk moments")
    
    print(f"\n✅ Simulation complete!")
    print(f"   Total steps: {step}")
    print(f"   Total color updates: {color_updates:,}")
    print(f"   Collision warnings detected: {collision_warnings:,}")
    print(f"   High-risk moments (CSV): {high_risk_moments:,}")

except KeyboardInterrupt:
    print("\n⚠️  Simulation interrupted by user")

except Exception as e:
    print(f"\n❌ Error during simulation: {e}")
    import traceback
    traceback.print_exc()

finally:
    traci.close()
    print("\n👋 TraCI connection closed")

print("\n" + "="*70)
print(" ✅ RISK VISUALIZATION COMPLETE!")
print("="*70)
print("\n📊 Color Legend:")
print("   🔴 RED   = SUMO Collision Warning OR High Risk (CSV)")
print("   🟢 GREEN = Medium Risk (CSV)")
print("   🔵 BLUE  = Low Risk (CSV)")
print("\n💡 Tip: Use OBS Studio or Windows Game Bar (Win+G) to record the simulation!")
print("="*70)