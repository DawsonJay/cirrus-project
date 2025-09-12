# Cirrus Project - Project Structure

**Last Updated:** September 12, 2025  
**Project:** AI Wildfire Prediction System

## Current Project Structure

```
cirrus-project/
├── README.md                              # Main project documentation
├── docs/                                  # Project documentation
│   ├── ai-wildfire-prediction-plan.md    # Complete implementation plan
│   ├── current-status.md                 # Current development status
│   ├── project-structure.md              # This file
│   ├── chat-records/                     # Development chat records
│   ├── dev-logs/                         # Historical development logs
│   └── development-logs/                 # Additional development logs
├── frontend/                             # React/TypeScript visualization
│   ├── src/
│   │   ├── components/                   # React components
│   │   │   ├── layout/                   # Layout components
│   │   │   ├── map/                      # Map visualization components
│   │   │   └── ui/                       # UI components
│   │   ├── contexts/                     # React contexts
│   │   ├── hooks/                        # Custom React hooks
│   │   ├── pages/                        # Page components
│   │   ├── theme/                        # Theme configuration
│   │   ├── types/                        # TypeScript type definitions
│   │   └── utils/                        # Utility functions
│   ├── public/                           # Static assets
│   │   └── assets/maps/                  # SVG map files
│   ├── design/                           # Design specifications and assets
│   ├── build/                            # Production build output
│   ├── node_modules/                     # Node.js dependencies
│   ├── package.json                      # Node.js dependencies
│   ├── package-lock.json                 # Dependency lock file
│   ├── tsconfig.json                     # TypeScript configuration
│   └── Dockerfile                        # Frontend containerization
├── data/                                 # Data storage and processing
│   ├── models/                           # Trained AI models (future)
│   ├── processed/                        # Processed weather data (future)
│   ├── raw/                              # Raw NOAA data (future)
│   └── weather_pool.db                   # Legacy database (to be replaced)
└── scripts/                              # Data processing scripts
    └── extract_historical_data.py        # NOAA data extraction script
```

## Directory Purposes

### `/docs/` - Documentation
- **Purpose**: Project documentation and development records
- **Key Files**: 
  - `ai-wildfire-prediction-plan.md` - Complete implementation roadmap
  - `current-status.md` - Current development status and progress
  - `project-structure.md` - This file explaining project organization
- **Subdirectories**:
  - `chat-records/` - Development conversation records
  - `dev-logs/` - Historical development logs
  - `development-logs/` - Additional development documentation

### `/frontend/` - User Interface
- **Purpose**: Interactive wildfire risk visualization
- **Technology**: React, TypeScript, SVG
- **Key Features**:
  - Interactive Canadian map
  - Daily risk slider navigation
  - Color-coded risk visualization
  - Responsive design
- **Status**: Existing codebase to be adapted for wildfire prediction

### `/data/` - Data Management
- **Purpose**: Storage for weather data and AI models
- **Current State**: Legacy database from previous weather system
- **Future State**: 
  - `raw/` - Downloaded NOAA historical data
  - `processed/` - Filtered and cleaned data for AI training
  - `models/` - Trained XGBoost models
- **Size**: Will be ~1.5-2GB total (optimized for essential parameters)

### `/scripts/` - Data Processing
- **Purpose**: Data preparation and AI model training scripts
- **Current**: `extract_historical_data.py` (legacy)
- **Future**: 
  - Data download and filtering scripts
  - Feature engineering scripts
  - AI model training scripts
  - Prediction generation scripts

## Architectural Decisions

### Removed Components
- **Backend APIs**: Eliminated real-time data collection
- **Weather Data Service**: Removed unnecessary server infrastructure
- **Database Dependencies**: Moved to local data processing
- **Server Infrastructure**: Chose static deployment approach

### Retained Components
- **Frontend**: Existing React/TypeScript codebase
- **Map System**: SVG-based Canadian map visualization
- **Documentation**: Comprehensive project documentation
- **Data Structure**: Organized data management approach

### New Components (Planned)
- **AI Model Training**: XGBoost wildfire prediction
- **Data Processing**: Historical NOAA data preparation
- **Prediction Generation**: 365 daily risk maps
- **Static Deployment**: Zero-cost hosting solution

## Development Workflow

### Phase 1: Data Preparation
1. Download NOAA historical weather data
2. Filter to essential wildfire parameters (TMAX, TMIN, PRCP, SNWD)
3. Process and clean data for AI training
4. Store in `/data/processed/`

### Phase 2: AI Development
1. Engineer features for wildfire prediction
2. Train XGBoost model on historical data
3. Generate 365 daily predictions for 2025
4. Save model and predictions in `/data/models/`

### Phase 3: Frontend Integration
1. Adapt existing map components for wildfire visualization
2. Implement daily risk slider
3. Add color-coded risk display
4. Test interactive functionality

### Phase 4: Deployment
1. Generate static frontend build
2. Deploy to free hosting (Vercel/Netlify)
3. Test end-to-end functionality
4. Document final system

## File Organization Principles

### Documentation
- **Centralized**: All docs in `/docs/` directory
- **Categorized**: Separate by type (plans, status, logs)
- **Versioned**: Include dates in filenames
- **Comprehensive**: Cover all aspects of development

### Code Organization
- **Frontend**: React component-based architecture
- **Data**: Organized by processing stage (raw → processed → models)
- **Scripts**: Single-purpose data processing tools
- **Types**: TypeScript definitions for type safety

### Asset Management
- **Maps**: SVG files in `/frontend/public/assets/maps/`
- **Design**: UI specifications in `/frontend/design/`
- **Build**: Production output in `/frontend/build/`
- **Data**: Large files in `/data/` (gitignored)

## Future Expansion

### Potential Additions
- **Multiple Disaster Types**: Floods, heat waves, etc.
- **Real-time Updates**: Weather API integration
- **Mobile App**: React Native version
- **API Service**: Backend for dynamic predictions

### Scalability Considerations
- **Data Growth**: Plan for additional years of data
- **Model Updates**: Retraining with new data
- **Feature Additions**: New weather parameters
- **Geographic Expansion**: Other countries/regions

## Maintenance

### Regular Tasks
- **Data Updates**: Annual historical data refresh
- **Model Retraining**: Periodic model updates
- **Frontend Updates**: UI/UX improvements
- **Documentation**: Keep docs current with changes

### Monitoring
- **Performance**: Frontend load times
- **Accuracy**: Model prediction quality
- **Usage**: User interaction patterns
- **Costs**: Hosting and data expenses (currently $0)

This structure supports the AI wildfire prediction system while maintaining clean organization and clear separation of concerns.
