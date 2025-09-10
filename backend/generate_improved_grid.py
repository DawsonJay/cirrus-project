#!/usr/bin/env python3
"""
Generate improved grid with even coverage
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.improved_grid_generator import ImprovedGridGenerator

def main():
    print("🌍 Generating improved grid with even coverage...")
    
    # Create generator for 10K points
    generator = ImprovedGridGenerator(target_points=10000)
    
    # Generate and populate database
    success = generator.populate_database()
    
    if success:
        print("✅ Grid generated successfully!")
        
        # Get and display stats
        stats = generator.get_grid_stats()
        print(f"\n📊 Grid Statistics:")
        print(f"   Total points: {stats.get('total_points', 0)}")
        print(f"   Regions: {stats.get('regions', 0)}")
        print(f"   Latitude range: {stats.get('min_lat', 0):.1f}° to {stats.get('max_lat', 0):.1f}°")
        print(f"   Longitude range: {stats.get('min_lon', 0):.1f}° to {stats.get('max_lon', 0):.1f}°")
        
        if 'actual_lat_spacing_km' in stats:
            print(f"   Actual spacing: {stats['actual_lat_spacing_km']:.1f} km (lat), {stats['actual_lon_spacing_km']:.1f} km (lon)")
        
        print(f"\n🗺️  Region Breakdown:")
        for region, count in stats.get('region_breakdown', {}).items():
            print(f"   {region}: {count} points")
        
        # Analyze coverage quality
        print(f"\n🔍 Coverage Analysis:")
        coverage = generator.analyze_coverage()
        if 'error' not in coverage:
            print(f"   Average spacing: {coverage['average_spacing_km']:.1f} km")
            print(f"   Spacing range: {coverage['min_spacing_km']:.1f} - {coverage['max_spacing_km']:.1f} km")
            print(f"   Consistency: {coverage['spacing_consistency']}")
        else:
            print(f"   Error: {coverage['error']}")
        
        # Test coordinate retrieval
        coords = generator.get_coordinates_for_batch()
        print(f"\n🧪 Test Results:")
        print(f"   Coordinates retrieved: {len(coords)}")
        if coords:
            print(f"   Sample coordinates: {coords[:3]}")
        
    else:
        print("❌ Failed to generate grid")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
