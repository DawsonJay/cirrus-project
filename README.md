# Cirrus Project - AI Wildfire Prediction System

**Last Updated:** September 12, 2025  
**Project:** Canadian AI Wildfire Prediction System  
**Status:** In Development - Data Preparation Phase

## Project Overview

The Cirrus Project is an AI-powered wildfire prediction system that generates daily wildfire risk maps for Canada using historical weather data and machine learning. The system uses XGBoost to predict wildfire risk based on weather patterns and displays results through an interactive frontend.

## System Architecture

### Core Components
- **Data Preparation**: Historical NOAA weather data processing (2015-2025)
- **AI Model**: XGBoost gradient boosting for wildfire risk prediction
- **Prediction Generation**: 365 daily wildfire risk maps for 2025
- **Frontend**: Interactive SVG map with daily risk visualization

### Key Features
- **Historical Data Focus**: Uses 10 years of Canadian weather data
- **Wildfire-Specific**: Optimized for wildfire risk prediction
- **Cost-Effective**: Zero ongoing costs (static deployment)
- **Interactive Visualization**: Daily slider with color-coded risk levels
- **Geographic Coverage**: All of Canada with regional risk assessment

## Technical Approach

### Data Strategy
- **Source**: NOAA GHCN-Daily historical weather data
- **Parameters**: Temperature (TMAX, TMIN), Precipitation (PRCP), Snow Depth (SNWD)
- **Processing**: One-time data preparation and filtering
- **Size**: ~1.5-2GB (optimized for essential parameters only)

### AI Implementation
- **Algorithm**: XGBoost (Gradient Boosting)
- **Training**: Historical data (2015-2024)
- **Prediction**: Historical averages for future dates
- **Output**: Risk scores (0-100%) for geographic regions

### Deployment
- **Frontend**: Static hosting (Vercel/Netlify/GitHub Pages)
- **Data Processing**: Local development machine
- **No Backend**: Pure client-side application
- **Cost**: $0/month (vs $20-25/month for cloud AI)

## Project Structure

```
cirrus-project/
├── docs/
│   ├── ai-wildfire-prediction-plan.md    # Complete implementation plan
│   └── chat-records/                     # Development documentation
├── frontend/                             # React/TypeScript visualization
│   ├── src/
│   │   ├── components/                   # Map and UI components
│   │   ├── hooks/                        # Custom React hooks
│   │   └── utils/                        # Coordinate transformation utilities
│   └── public/                           # Static assets
├── data/                                 # Historical weather data
│   ├── raw/                             # Original NOAA data
│   ├── processed/                       # Filtered and cleaned data
│   └── models/                          # Trained AI models
└── scripts/                             # Data processing scripts
    └── extract_historical_data.py       # NOAA data extraction
```

## Development Phases

### Phase 1: Data Preparation (Current)
- [ ] Download NOAA historical weather data
- [ ] Filter to essential wildfire parameters
- [ ] Process and clean data for AI training
- [ ] Validate data quality and coverage

### Phase 2: AI Model Development
- [ ] Set up XGBoost training pipeline
- [ ] Engineer features for wildfire prediction
- [ ] Train and validate model
- [ ] Generate 365 daily predictions

### Phase 3: Frontend Development
- [ ] Create SVG map visualization
- [ ] Build interactive daily slider
- [ ] Implement color-coded risk display
- [ ] Deploy to static hosting

### Phase 4: Integration & Testing
- [ ] Connect all components
- [ ] Test end-to-end workflow
- [ ] Optimize performance
- [ ] Document system

## Key Decisions

### Architectural Pivots
1. **Removed Weather Data Service**: Eliminated unnecessary server infrastructure
2. **Removed Backend APIs**: Moved away from real-time data collection
3. **Focused on AI/ML**: Concentrated on core prediction capabilities
4. **Static Deployment**: Chose cost-effective frontend-only approach

### Technical Choices
- **XGBoost**: Selected for tabular weather data and interpretability
- **Historical Data**: Chose over real-time APIs for reliability and cost
- **Static Frontend**: Eliminated backend complexity and ongoing costs
- **Local Processing**: Moved AI training and prediction generation to local machine

## Portfolio Value

### Technical Skills Demonstrated
- **AI/ML Development**: XGBoost model training and optimization
- **Data Science**: Feature engineering and data preparation
- **Frontend Development**: Interactive data visualization
- **System Design**: Cost-effective architecture decisions
- **Strategic Thinking**: Recognizing and eliminating unnecessary complexity

### Business Skills Shown
- **Cost Optimization**: $0/month vs $20-25/month alternatives
- **Problem-Solving**: Working within constraints and requirements
- **Focus**: Concentrating on core value proposition
- **Pragmatism**: Choosing the right tool for the job

## Getting Started

### Prerequisites
- Python 3.8+ with data science libraries (pandas, scikit-learn, xgboost)
- Node.js 16+ for frontend development
- 10GB+ storage for data and models

### Development Setup
1. Clone the repository
2. Install Python dependencies for data processing
3. Install Node.js dependencies for frontend
4. Follow the implementation plan in `docs/ai-wildfire-prediction-plan.md`

## Documentation

- **Implementation Plan**: `docs/ai-wildfire-prediction-plan.md`
- **Development Records**: `docs/chat-records/`
- **Architecture Decisions**: Portfolio records in `portfolio-profile/`

## License

This project is part of a portfolio demonstration and is not intended for commercial use.