# Driver Behaviour Analysis and Collision Risk Warning System for Kerala Road Conditions

> A SUMO-based traffic simulation and machine-learning pipeline for analysing microscopic driver behaviour and classifying vehicle situations into **Low, Medium, and High collision-risk levels** under simulated sensor uncertainty.

---

## 📌 Overview

Road traffic in Kerala consists of highly heterogeneous traffic involving two-wheelers, cars, autorickshaws, buses, trucks, mini-trucks, and cycles. This heterogeneous environment creates complex interactions between vehicles, particularly during close following, sudden braking, lane changes, junction movements, and conflict situations.

This project develops a **driver behaviour analysis and collision-risk classification system** using microscopic vehicle trajectory data.

The system processes vehicle trajectory information generated from **SUMO (Simulation of Urban Mobility)**, extracts behavioural and surrogate safety features, generates collision-risk labels using a rule-based risk-scoring framework, introduces calibrated sensor noise to approximate real-world measurement uncertainty, and trains a **Random Forest classifier** to classify traffic situations into:

* 🟢 **Low Risk**
* 🟡 **Medium Risk**
* 🔴 **High Risk**

The project is designed around traffic conditions representative of **Kerala**, with the Kulathoor study area used as the traffic context.

> **Important:** This project is a surrogate collision-risk classification system. The target labels are derived from safety-related traffic features rather than independently observed crash outcomes. Therefore, the model should not be interpreted as directly predicting the probability of an actual crash.

---

# 🎯 Objectives

The main objectives of the project are:

1. Analyse microscopic vehicle trajectories under Kerala-like traffic conditions.
2. Extract meaningful driver-behaviour and vehicle-interaction features.
3. Identify potentially risky traffic situations using surrogate safety measures.
4. Develop a multi-class collision-risk classification model.
5. Introduce realistic measurement uncertainty into simulated data.
6. Evaluate the model using multiple validation strategies.
7. Test model behaviour under safety-critical traffic scenarios.
8. Provide a foundation for a real-time collision-risk warning system.

---

# 🏗️ System Architecture

```text
                    KERALA / KULATHOOR TRAFFIC CONTEXT
                                  │
                                  ▼
                         Traffic Volume Data
                                  │
                                  ▼
                       SUMO Traffic Simulation
                                  │
                                  ▼
                        Vehicle Trajectories
                                  │
                                  ▼
                           FCD XML Output
                                  │
                                  ▼
                     ┌──────────────────────┐
                     │ Data Preprocessing   │
                     │                      │
                     │ • XML parsing        │
                     │ • Vehicle mapping    │
                     │ • Sorting            │
                     │ • Cleaning           │
                     └──────────┬───────────┘
                                │
                                ▼
                  ┌─────────────────────────────┐
                  │ Feature Extraction          │
                  │                             │
                  │ • Speed                    │
                  │ • Acceleration             │
                  │ • Heading change           │
                  │ • Lane change              │
                  │ • Following gap            │
                  │ • Relative speed           │
                  │ • PET                      │
                  │ • Junction context         │
                  └─────────────┬───────────────┘
                                │
                                ▼
                     Surrogate Risk Scoring
                                │
                                ▼
                       Low / Medium / High
                                │
                                ▼
                  Calibrated Sensor Noise
                                │
                                ▼
                       Feature Engineering
                                │
                                ▼
                    Random Forest Classifier
                                │
                                ▼
                  ┌─────────────────────────┐
                  │ Risk Classification     │
                  │                         │
                  │ LOW / MEDIUM / HIGH     │
                  └────────────┬────────────┘
                               │
                               ▼
                     Scenario Safety Tests
                               │
                               ▼
                  Collision-Risk Warning Logic
```

---

# 🔬 Methodology

## 1. Traffic Simulation and FCD Generation

The project uses **SUMO (Simulation of Urban Mobility)** to model vehicle movement and generate Floating Car Data (FCD).

The FCD contains vehicle-level information at individual simulation timesteps, including:

* Timestamp
* Vehicle ID
* Vehicle type
* Speed
* Position
* X/Y coordinates
* Lane
* Heading/angle
* Slope

The FCD is stored in XML format and subsequently converted into a tabular dataset.

---

# 2. FCD Parsing

The XML FCD file is parsed using Python's `xml.etree.ElementTree`.

Each vehicle observation is converted into a row containing:

| Feature        | Description               |
| -------------- | ------------------------- |
| `timestamp`    | Simulation time           |
| `vehicle_id`   | Unique vehicle identifier |
| `vehicle_type` | Vehicle category          |
| `speed_ms`     | Vehicle speed in m/s      |
| `angle`        | Vehicle heading           |
| `lane`         | Current lane              |
| `pos`          | Position along the lane   |
| `x`, `y`       | Spatial coordinates       |
| `slope`        | Road slope                |

The resulting records are stored in a Pandas DataFrame for subsequent processing.

---

# 3. Vehicle Type Normalisation

SUMO vehicle definitions can contain simulation-specific vehicle types such as:

```text
tw_aggressive
tw_normal
tw_harsh
tw_cautious
car_normal
car_aggressive
bus_normal
truck_aggressive
```

These are mapped into broader vehicle categories:

```text
twowheeler
car
auto
bus
truck
minitruck
cycle
```

This prevents the model from unnecessarily treating behavioural naming variations within the simulation as completely different vehicle classes.

---

# 4. Temporal Feature Extraction

The trajectory data is sorted by:

```text
vehicle_id → timestamp
```

This allows temporal changes in vehicle behaviour to be calculated.

## 4.1 Acceleration

Acceleration is calculated using:

$$
a = \frac{\Delta v}{\Delta t}
$$

where:

* \(v\) = vehicle speed
* \(t\) = timestamp

The implementation handles zero timestep differences to prevent division-by-zero errors.

### Why acceleration?

Speed alone does not describe aggressive driving behaviour. Sudden acceleration and deceleration provide additional information about vehicle behaviour.

---

## 4.2 Heading Change

Heading change is calculated from consecutive vehicle angles.

The angular difference is normalized to:

$$
[-180^\circ,180^\circ]
$$

This avoids incorrect results caused by the 0°/360° boundary.

For example:

```text
359° → 1°
```

represents approximately:

```text
+2°
```

rather than:

```text
-358°
```

---

## 4.3 Lane Change

A lane change is detected when the vehicle's lane identifier differs from its previous observation.

```text
Previous lane = lane_1
Current lane  = lane_2

Lane change = 1
```

Otherwise:

```text
Lane change = 0
```

---

## 4.4 Speed Conversion

SUMO provides speed in m/s.

The project converts it into km/h:

$$
Speed_{km/h}=Speed_{m/s}\times3.6
$$

---

# 5. Spatial Interaction Features

Driver risk is not determined only by individual vehicle behaviour. Interactions with surrounding vehicles are also important.

The project therefore extracts:

* Gap to leader
* Relative speed to leader

---

## 5.1 Gap to Leader

Vehicles are grouped by:

```text
timestamp
lane
```

and sorted according to their longitudinal position.

The distance between a following vehicle and the vehicle immediately ahead is used as:

```text
gap_to_leader_m
```

Only vehicles in the same lane are considered for this following-gap calculation.

A default sentinel value of:

```text
999 m
```

is used when no valid leader is identified.

---

## 5.2 Relative Speed

Relative speed is calculated as:

$$
V_{relative}=V_{follower}-V_{leader}
$$

For example:

```text
Follower = 60 km/h
Leader   = 40 km/h

Relative speed = +20 km/h
```

A positive value indicates that the following vehicle is closing on the leader.

### Why combine gap and relative speed?

A small gap does not necessarily mean an immediate danger if both vehicles are travelling at the same speed.

However:

```text
Small gap
+
High closing speed
```

indicates a rapidly developing interaction.

---

# 6. Enhanced Post-Encroachment Time (PET)

## What is PET?

**Post-Encroachment Time (PET)** is a surrogate safety measure used to describe the temporal separation between road users occupying a potential conflict area.

A small PET indicates that two vehicles passed through a potential conflict region with little temporal separation.

---

## Multi-Radius PET

The project calculates PET using three spatial conflict radii:

```text
3 m
6 m
10 m
```

Vehicle trajectories are converted into spatial cells at each radius.

For each cell, the system records:

* vehicle entering time
* vehicle exiting time

If another vehicle subsequently enters the same conflict cell, the temporal separation can be calculated as:

$$
PET=t_{entry,B}-t_{exit,A}
$$

The minimum valid PET detected across the conflict radii is retained.

---

## Why Multiple Radii?

A single spatial resolution can be sensitive to the exact trajectory geometry.

Using:

```text
3 m
6 m
10 m
```

allows conflict detection at multiple spatial scales.

The minimum valid PET across these scales is retained as the conflict indicator.

> The implemented PET calculation is a cell-based approximation. A future implementation could use continuous trajectory interpolation and explicit geometric conflict-point detection.

---

# 7. Behavioural Indicators

Several binary behavioural indicators are extracted.

## Hard Braking

A hard-braking event is identified when:

```text
acceleration < -2.0 m/s²
```

while:

```text
speed > 5 km/h
```

---

## Hard Acceleration

A hard-acceleration event is identified when:

```text
acceleration > 2.0 m/s²
```

while the vehicle is moving.

---

## Erratic Steering

A potential erratic-steering event is identified when:

```text
|heading change| > 15°
```

while the vehicle is moving.

---

## Junction Detection

SUMO junction lanes are identified through lane identifiers beginning with:

```text
:
```

This is used to create:

```text
in_junction
```

---

## Wrong-Way Driving

Wrong-way driving was considered but excluded from the feature set.

The standard SUMO routing configuration enforces permitted travel directions, so vehicles are not expected to travel against traffic in the simulated network.

Including an almost-always-zero feature would not provide useful predictive information.

---

# 8. Surrogate Risk Scoring

Because the trajectory data does not contain an independently observed crash outcome for every observation, the project constructs a surrogate risk score.

The score incorporates:

* PET
* Following gap
* Relative speed
* Speed
* Deceleration
* Heading change
* Vehicle type
* Vulnerability

---

## PET Contribution

| PET          | Risk Score Contribution |
| ------------ | ----------------------: |
| `< 1.5 s`    |                      +7 |
| `1.5–3.0 s`  |                      +5 |
| `3.0–5.0 s`  |                      +3 |
| `5.0–10.0 s` |                      +1 |

Lower PET therefore contributes more strongly to the risk score.

---

## Gap Contribution

For moving vehicles with a detected leader:

| Gap     | Score |
| ------- | ----: |
| `< 2 m` |    +4 |
| `< 4 m` |    +2 |
| `< 6 m` |    +1 |

Additional points are assigned when the vehicle is rapidly closing on its leader.

---

## Vehicle-Specific Speed Thresholds

Different vehicle classes use different speed thresholds.

### Two-wheelers / Cycles

```text
>25 km/h → +1
>40 km/h → +2
>55 km/h → +3
```

### Cars / Autos

```text
>35 km/h → +1
>50 km/h → +2
>65 km/h → +3
```

### Buses / Trucks / Mini-trucks

```text
>30 km/h → +1
>40 km/h → +2
>50 km/h → +3
```

---

## Deceleration Contribution

```text
a < -1.5 m/s² → +1
a < -2.0 m/s² → +2
a < -3.0 m/s² → +3
```

---

## Heading Change Contribution

```text
> 8°  → +1
>15°  → +2
>30°  → +3
```

---

## Vehicle Vulnerability

Additional risk points are applied for certain vehicle categories and interaction conditions.

For example, close following by two-wheelers receives additional weight because of their greater vulnerability in vehicle interactions.

---

# 9. Risk Categories

The numerical risk score is converted into three categories:

```text
Score < 4       → LOW
Score 4–7       → MEDIUM
Score ≥ 8       → HIGH
```

A small Gaussian boundary jitter with:

$$
N(0,0.8)
$$

is applied to the clean score before final label assignment.

The purpose is to introduce uncertainty around borderline cases rather than creating perfectly deterministic class boundaries.

---

# ⚠️ Important Label Interpretation

The generated `collision_risk` value is a **surrogate risk label**, not an independently observed crash label.

Therefore:

```text
Random Forest prediction
```

should be interpreted as:

> Classification of the engineered surrogate risk construct under noisy observations.

It should **not** be interpreted as:

> Direct prediction of the probability that a real-world crash will occur.

Independent crash or near-crash datasets would be required to make that stronger claim.

---

# 10. Simulated Sensor Noise

SUMO produces relatively clean simulation data compared with real-world vehicle sensors.

To improve robustness, calibrated noise is introduced into the input features.

| Feature        | Noise / Uncertainty                      |
| -------------- | ---------------------------------------- |
| Speed          | \(N(0,1.0)\) km/h                        |
| Acceleration   | \(N(0,0.15)\) m/s²                       |
| Heading change | \(N(0,1.0)\) degrees                     |
| Gap            | \(N(0,0.8)\) m for realistic gaps        |
| Relative speed | \(N(0,1.0)\) km/h                        |
| PET            | 10% missing detection for borderline PET |
| PET            | \(N(0,0.1)\) s jitter                    |
| Risk score     | \(N(0,0.8)\) boundary jitter             |

The labels are generated **before feature noise is introduced** and are then kept fixed.

This allows the model to learn the risk categories from imperfect observations.

---

# 11. Feature Engineering

Additional physically motivated features are created before model training.

## PET Capping

PET values above 15 seconds are capped:

```python
pet_s_capped = pet_s.clip(upper=15)
```

The raw PET sentinel value of `999` represents an unavailable PET rather than a physical 999-second PET.

---

## Gap Capping

Gap values are capped at:

```text
60 m
```

to prevent the sentinel value of `999` from being interpreted as an extremely large physical following distance.

---

## Closing Severity

$$
ClosingSeverity=
\frac{RelativeSpeed}{Gap+0.1}
$$

for vehicles that are actively closing on a leader.

The `0.1` term prevents division by zero.

---

## Kinetic Risk

$$
KineticRisk=
Speed\times|NegativeAcceleration|
$$

This combines speed and strong deceleration into a single physically motivated feature.

---

## PET Urgency

$$
PETUrgency=
\frac{Speed}{PET+0.1}
$$

This increases when:

* speed is high
* PET is low

---

## Vulnerability

$$
Vulnerability=
\frac{Speed}{Gap+1}
$$

for vehicles with a detected leader.

---

# 12. Machine Learning Model

## Random Forest Classifier

The project uses a **Random Forest classifier** for three-class classification.

The model contains:

```text
500 decision trees
```

with:

```text
max_depth = 15
min_samples_leaf = 20
min_samples_split = 40
max_features = sqrt
```

Class weights are calculated using balanced class weighting.

---

# 🌲 Why Random Forest?

Random Forest was selected because the problem contains:

* nonlinear relationships
* threshold-based behaviour
* interactions between multiple physical variables
* mixed feature types
* measurement noise

Random Forest does not require feature scaling and can model nonlinear relationships without assuming a specific functional form.

It also provides feature-importance information that can help interpret the model.

---

# 13. Model Features

The final Random Forest model uses 11 features:

```text
1.  speed_kmph
2.  acceleration_ms2
3.  gap_capped
4.  relative_speed_kmph
5.  pet_s_capped
6.  heading_change_deg
7.  vehicle_type_enc
8.  closing_severity
9.  kinetic_risk
10. pet_urgency
11. vulnerability
```

The target variable is:

```text
collision_risk
```

with three classes:

```text
low
medium
high
```

---

# 14. Vehicle Type Encoding

The categorical vehicle type is converted to numerical values using `LabelEncoder`.

For example:

```text
car
twowheeler
bus
truck
...
```

are converted into numerical representations for use by the Random Forest.

---

# 15. Train-Test Split

The dataset is divided into:

```text
75% Training
25% Testing
```

using stratification.

Stratification ensures that the class distribution is approximately maintained between training and testing sets.

A fixed random state is used for reproducibility.

---

# 16. Class Weighting

Balanced class weights are calculated from the training data.

This helps prevent the classifier from simply favouring the majority class when the three risk categories have different frequencies.

Instead of generating synthetic observations, class weighting modifies the importance of classification errors during training.

---

# 17. Model Evaluation

The model is evaluated using multiple complementary methods.

---

## Test 1 — Held-Out Test Set

The model is evaluated on the 25% test set using:

* Accuracy
* Precision
* Recall
* F1-score
* Confusion matrix

---

## Test 2 — Stratified 5-Fold Cross-Validation

Five-fold stratified cross-validation is performed using:

* Accuracy
* Macro F1
* Weighted F1

### Macro F1

Each class receives equal importance.

This is useful when the performance of all risk classes matters rather than only the most common class.

---

# 18. Vehicle-Wise Group K-Fold

A particularly important validation strategy is **vehicle-wise GroupKFold**.

The vehicle ID is used as the grouping variable.

Therefore, observations from the same vehicle are prevented from appearing in both training and validation portions of the same fold.

### Why?

Vehicle trajectories are temporally correlated.

For example:

```text
Vehicle A
 ├── t1
 ├── t2
 ├── t3
 ├── t4
 └── t5
```

A random split might place `t1–t4` in training and `t5` in testing.

This can make the model appear better than it actually is.

GroupKFold instead evaluates:

> Can the model generalize to vehicles it has never seen during training?

This provides a more demanding estimate of generalization.

---

# 19. ROC-AUC

The model also calculates multi-class ROC-AUC using a one-vs-rest strategy.

Each class is evaluated against the remaining classes:

```text
Low vs Rest
Medium vs Rest
High vs Rest
```

This provides an additional measure of class separability beyond accuracy.

---

# 20. Prediction Confidence

The model's predicted probability distribution is also examined.

For each sample:

```python
max(predicted_class_probabilities)
```

is used as the maximum model confidence.

The analysis reports:

* Mean prediction confidence
