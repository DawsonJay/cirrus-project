# AI Design Decisions

## Core Concept
- **Single target**: Wildfire probability prediction only (0.0 to 1.0)
- **No weather prediction**: Use existing weather data as features
- **Temporal separation**: Only use data 1+ years older than prediction date
- **3D grid structure**: Every cell-date combination has both weather and wildfire data

## Data Structure
- **Training data**: Historical cell-date combinations with known fire status
- **Test data**: Future cell-date combinations to predict
- **Features**: Weather data (temperature, humidity, precipitation, etc.) + temporal/seasonal patterns
- **Target**: `fire_occurred` (0 or 1) from `wildfire_data` table

## Competition Framework
- **Evolution**: AIs compete to find best data selection strategies and feature engineering approaches
- **Each AI**: Has its own XGBoost model with unique configuration
- **Training**: Each AI trains its own model on its selected historical data
- **Competition**: AIs predict the same test samples, best performers survive

## Evaluation Metrics
- **Primary metric**: Log Loss (Cross-Entropy)
- **Formula**: `Score = -[y * log(p) + (1-y) * log(1-p)]`
- **Goal**: Calibrated probabilities (90% prediction = 90% actual fire rate)
- **Lower scores are better**

## Scoring Philosophy
- **Reward**: Higher predictions when fires occur, lower predictions when no fires
- **Penalty**: Higher predictions when no fires, lower predictions when fires occur
- **Focus**: Calibrated risk maps with mostly low scores and accurate high-risk areas

## Expected Output
- **Risk maps**: Mostly very low scores (0.01-0.1) with some high-risk areas (0.7-0.9)
- **High-risk areas**: Should be accurate (predicted 90% = actual 90% fire rate)
- **Use case**: Practical wildfire risk assessment for decision making

## Technical Implementation
- **XGBoost**: One model per AI for binary classification
- **Class imbalance**: Handle with `scale_pos_weight` and proper evaluation
- **Parallel processing**: Train multiple AIs concurrently
- **Timeouts**: Prevent hanging during training (30s per model)
- **Seed AI**: Pre-trained baseline to initialize population

## Data Pipeline Integration
- **Stage 5**: Creates complete wildfire dataset (both fire and no-fire records)
- **Wildfire data**: `fire_occurred` field (0 or 1) for all cell-date combinations
- **Temporal split**: Train on 2022-2023, test on 2024 data

## Training Data Strategy (FINAL)
- **Approach**: Fixed comprehensive dataset (no data selection evolution)
- **Target cells**: Diverse selection across Canadian territories
- **Historical patterns**: 1+ years older than target date (realistic prediction scenario)
- **Pattern types**: Seasonal, yearly, spatial patterns (NO recent patterns)
- **Balance**: Both fire and no-fire examples
- **Geographic diversity**: Different regions and seasons
- **Temporal separation**: Training data 1+ years older than prediction dates
- **Critical constraint**: No recent patterns (same year) to match prediction scenario

## Training Sample Structure
```
Target: Cell 12345 on 2023-06-15 (1+ years ago)
Historical patterns (1+ years older):
  - Cell 12345 on 2022-06-08 to 2022-06-22 (yearly pattern, ±7 days)
  - Cell 12345 on 2021-06-08 to 2021-06-22 (yearly pattern, ±7 days)
  - Cell 12345 on 2020-06-08 to 2020-06-22 (yearly pattern, ±7 days)
  - Cell 12346 on 2022-06-15 (spatial pattern, same date)
  - Cell 12347 on 2022-06-15 (spatial pattern, same date)
  - Cell 12346 on 2021-06-08 to 2021-06-22 (spatial + yearly pattern)
  - etc.
Target: fire_occurred = 1 (actual fire happened)
```

## Pattern Window Specifications
- **Yearly patterns**: ±7 days around same date (2-week window)
- **Spatial patterns**: Same date (1+ years ago)
- **Spatial + yearly patterns**: ±7 days around same date (1+ years ago)
- **Weather features**: Aggregated over windows (avg, min, max, total, count)

## Feature Engineering Strategy (FINAL)
- **Approach**: Aggregate by pattern type (not individual cells)
- **Same cell yearly patterns**: 3 years of data, aggregated features
- **Neighbor spatial patterns**: 8 neighbors, aggregated features
- **Target cell features**: Terrain, area, historical fire frequency
- **Total features**: ~20 per target cell (manageable and comprehensive)

## Feature Breakdown
### **Same Cell Yearly Patterns (15 features)**
- Weather per year: avg_temp, max_temp, total_precip, dry_days, fire_occurred
- Aggregated: avg_temp_trend, fire_frequency, avg_fire_size

### **Neighbor Spatial Patterns (6 features)**
- neighbor_avg_temp, neighbor_max_temp, neighbor_total_precip
- neighbor_dry_days, neighbor_fire_frequency, neighbor_terrain_types

### **Target Cell Features (4 features)**
- terrain_type, area_km2, historical_fire_frequency, elevation

## Training Dataset Configuration
- **Training targets**: 500 fixed targets (same for all AIs)
- **Geographic stratification**: Forest (40%), Tundra (20%), Urban (20%), Other (20%)
- **Class balance**: Equal fire/no-fire examples per terrain type
- **Confidence filtering**: Terrain-specific thresholds (Forest: 0.4, Tundra: 0.3, Urban: 0.7)
- **Missing data**: Filter out targets with incomplete pattern data

## Testing Dataset Configuration
- **Large test pool**: 5,000+ diverse targets across all terrain types
- **Per generation**: Random subset of 200 targets (same for all AIs in generation)
- **Between generations**: Different random subset each generation
- **Purpose**: Fair competition + generalization pressure

## Evolution Configuration
- **Generations**: 10 (with smart convergence strategies)
- **Population size**: 50 AIs per generation
- **Selection**: Top 20% survive, elite preservation
- **Convergence**: Early stopping if no improvement for 3 generations
- **Testing fairness**: All AIs in generation tested on same targets

## XGBoost Parameters to Evolve
- **max_depth**: 3-15 (tree depth, deeper = slower)
- **n_estimators**: 50-500 (number of trees, more = slower)
- **learning_rate**: 0.01-0.3 (step size, lower = more trees needed)
- **subsample**: 0.6-1.0 (data sampling, less = faster)
- **colsample_bytree**: 0.6-1.0 (feature sampling, less = faster)
- **reg_alpha**: 0.0-10.0 (L1 regularization)
- **reg_lambda**: 0.0-10.0 (L2 regularization)
- **early_stopping_rounds**: 10-50 (stop early if no improvement)

## Performance Constraints
- **Prediction timeout**: 3 seconds per target (model fails if exceeded)
- **Speed pressure**: Evolution favors faster, simpler models
- **Practical deployment**: Ensures real-time prediction capability

## Evolution Operators
- **Crossover**: Blend crossover (random value between parents)
- **Mutation**: Adaptive mutation (big changes early, fine-tuning later)
- **Selection**: Top 5 best performers (simple and direct)
- **Breeding**: Top 5 AIs create 50 offspring for next generation
- **Elite preservation**: Best AI unchanged each generation

## Initial Population Strategy
- **Hybrid approach**: 5 AIs with smart defaults + 45 AIs with random parameters
- **Smart defaults**: max_depth=6, n_estimators=100, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8
- **Random parameters**: Full range exploration for remaining 45 AIs
- **Benefits**: Balance of quality and diversity, safety net for reasonable starting values

## Convergence Strategy
- **Hybrid approach**: Maximum 10 generations OR early stopping if no improvement for 3 generations
- **Early stopping**: Track best fitness each generation, stop if no improvement for 3 consecutive generations
- **Safety net**: Never exceed 10 generations (4-5 hour target runtime)
- **Benefits**: Stops when converged, prevents infinite runs, flexible timing

## Implementation Strategy
- **Incremental approach**: Build simple first, add complexity gradually
- **Phase 1**: Core framework (1-2 hours) - Basic AI class, simple training, basic evaluation
- **Phase 2**: Evolution (1-2 hours) - Population initialization, crossover/mutation, selection/breeding
- **Phase 3**: Production (1-2 hours) - Full dataset, parallel processing, convergence tracking
- **Benefits**: Easy to debug, verify each step, manageable chunks, fast feedback

## Next Steps
1. **Wait for Stage 5 completion** (interpolating wildfire data)
2. **Priority 1**: Create high-quality training and testing datasets
   - Load and examine the complete interpolated_grid_db.db
   - Verify data quality and completeness
   - Design comprehensive training data selection strategy
   - Create balanced, stratified training sets
   - Validate testing dataset diversity
3. **Phase 1**: Build core framework with basic AI class and simple training
4. **Phase 2**: Add evolution operators (crossover, mutation, selection)
5. **Phase 3**: Scale up to full production system with parallel processing

---
*Last updated: 2025-09-19*
