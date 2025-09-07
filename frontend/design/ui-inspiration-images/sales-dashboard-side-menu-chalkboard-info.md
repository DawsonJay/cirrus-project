# Sales Dashboard - Side Menu Chalkboard Design

**Image**: `sales-dashboard-side-menu-chalkboard.jpg`

## Design Elements

### Color Palette
- **Background**: Dark slate greys with chalkboard-like texture
- **Text**: White and light grey for high contrast
- **Accent Colors**: Bright teal, purple, green, orange, red, blue
- **Active States**: Teal highlighting for selected navigation items

### Navigation Design
- **Left Sidebar**: Narrow vertical navigation with clear icons
- **Icon System**: Home, notifications (with badge), bar chart (active), chat
- **User Profile**: Circular profile picture at top
- **Settings**: Gear icon and view settings at bottom
- **Visual Indicators**: Small circles for steps/pagination

### Layout Structure
- **Two-Section Main Area**:
  1. **Top Section**: Large "Total Sales" line graph with date range selector
  2. **Bottom Section**: 2x2 grid of data cards with metrics
- **Clean Hierarchy**: Clear separation between different data types
- **Rounded Corners**: Modern, soft aesthetic on cards

### Data Visualization
- **Line Graph**: Purple line with circular markers showing sales trends
- **Grid Background**: Subtle grid pattern for data reference
- **Date Range**: Teal pill-shaped button for time selection
- **Data Cards**: Four cards showing different product categories with:
  - Percentage changes (green ▲, red ▼)
  - Main values (32k, 431k, 12k, 8k)
  - Category names (Shoes, Clothing, Outerwear, Hats)
  - Small horizontal bar graphs

### Information Architecture
- **Progressive Disclosure**: Main view shows key metrics, deeper details available
- **Clear Categories**: Each data card represents a specific product category
- **Visual Hierarchy**: Large numbers, smaller labels, color-coded changes
- **Interactive Elements**: Clickable navigation, date selection, scrollable areas

## What You Like About This Design

### Key Preferences
- **Side Menu**: Clear icons that change the display of the main panel
- **Slate Grey with Bright Colors**: Dark chalkboard-like background with vibrant accents
- **Simple Chalkboard Design**: Clean, uncluttered aesthetic
- **Non-Overwhelming**: Doesn't overwhelm with information but has lots of ways to click deeper
- **Progressive Disclosure**: Main view shows essentials, details available on demand

### Design Principles to Apply
- Use clear icon-based navigation that changes main content
- Maintain dark slate background with bright accent colors
- Keep the main view simple and focused
- Provide multiple ways to access deeper information
- Use progressive disclosure to avoid information overload
- Include visual indicators for active states and notifications

## Application to Cirrus Project

### Potential Adaptations
- **Weather Navigation**: Side menu with icons for different weather types
- **Main Panel**: Large weather map or graph with data cards below
- **Data Cards**: Weather metrics (temperature, humidity, risk levels, precipitation)
- **Color Coding**: Weather-appropriate colors (blues for cold, reds for heat, greens for safe)

### Implementation Notes
- The side navigation would work perfectly for weather disaster types
- The chalkboard aesthetic would give a professional, technical feel
- The progressive disclosure approach would prevent weather data overload
- The data card system could show different weather metrics
- The clean hierarchy would make weather information easy to digest

### Weather-Specific Adaptations
- **Navigation Icons**: 
  - Home (overview)
  - Wildfires (fire icon)
  - Hailstorms (hail icon)
  - Tornadoes (tornado icon)
  - Floods (water icon)
  - Derechos (wind icon)
- **Main Panel**: Large weather map or risk assessment graph
- **Data Cards**: 
  - Temperature trends
  - Humidity levels
  - Risk assessments
  - Precipitation forecasts
- **Color Scheme**: Weather-appropriate gradients and accents
- **Interactive Elements**: Date range selection, location filtering, risk level toggles

### Technical Implementation
- **Material-UI**: Custom dark theme with chalkboard-like styling
- **Navigation**: Icon-based sidebar with active state management
- **Data Visualization**: Chart.js or D3.js for weather graphs and trends
- **Progressive Disclosure**: Modal dialogs or expandable sections for detailed data
- **Responsive Design**: Ensure sidebar and main content work on different screen sizes
