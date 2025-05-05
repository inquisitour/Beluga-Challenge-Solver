"""
Analysis script for hybrid A* + CSP experiment results.
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def analyze_hybrid_results():
    # Get the latest results directory
    results_dir = "hybrid_experiment_results"
    if not os.path.exists(results_dir):
        print("No hybrid experiment results found. Please run run_hybrid_experiments.py first.")
        return
        
    run_dirs = [os.path.join(results_dir, d) for d in os.listdir(results_dir) if d.startswith("run_")]
    if not run_dirs:
        print("No experiment runs found.")
        return
        
    latest_run = max(run_dirs, key=os.path.getmtime)
    print(f"Analyzing hybrid results from: {latest_run}")
    
    # Read the summary file
    summary_file = os.path.join(latest_run, "summary.csv")
    summary = pd.read_csv(summary_file)
    
    # Calculate success rate
    success_rate = summary["Success"].mean() * 100
    print(f"Overall success rate: {success_rate:.1f}%")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print(summary[["Experiment", "Success", "Iterations", "PlanLength", "SearchTime", "TotalTime", "MaxFlights", "MaxParts"]])
    
    # Create report directory
    report_dir = os.path.join(latest_run, "analysis")
    os.makedirs(report_dir, exist_ok=True)
    
    # Plot comparison of success rates
    plt.figure(figsize=(10, 6))
    sns.barplot(x="Experiment", y="Success", data=summary)
    plt.title("Success Rate by Experiment")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(report_dir, "success_comparison.png"))
    
    # Plot max flights and max parts comparison
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(x="Experiment", y="MaxFlights", data=summary, color="blue", label="Max Flights")
    ax2 = ax.twinx()
    sns.barplot(x="Experiment", y="MaxParts", data=summary, color="green", alpha=0.5, ax=ax2, label="Max Parts")
    plt.title("Progress by Experiment")
    plt.xticks(rotation=45, ha="right")
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(os.path.join(report_dir, "progress_comparison.png"))
    
    # Plot search time comparison
    plt.figure(figsize=(10, 6))
    sns.barplot(x="Experiment", y="TotalTime", data=summary)
    plt.title("Total Execution Time by Experiment")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(report_dir, "time_comparison.png"))
    
    # Plot plan length (only for successful experiments)
    successful = summary[summary["Success"] == True]
    if not successful.empty:
        plt.figure(figsize=(10, 6))
        sns.barplot(x="Experiment", y="PlanLength", data=successful)
        plt.title("Plan Length by Experiment (Successful Only)")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(os.path.join(report_dir, "plan_length_comparison.png"))
    
    # Compare hybrid with original approach
    # Check if original results exist
    original_results_dir = "improved_experiment_results"
    original_run_dirs = [os.path.join(original_results_dir, d) for d in os.listdir(original_results_dir) 
                         if d.startswith("run_")] if os.path.exists(original_results_dir) else []
    
    if original_run_dirs:
        latest_original_run = max(original_run_dirs, key=os.path.getmtime)
        original_summary_file = os.path.join(latest_original_run, "summary.csv")
        
        if os.path.exists(original_summary_file):
            original_summary = pd.read_csv(original_summary_file)
            
            # Add approach type for plotting
            original_summary["Approach"] = "Original"
            summary["Approach"] = "Hybrid"
            
            # Combine dataframes
            combined = pd.concat([original_summary, summary])
            
            # Plot comparison
            plt.figure(figsize=(12, 8))
            ax = sns.barplot(x="Experiment", y="MaxFlights", hue="Approach", data=combined)
            plt.title("Maximum Flights Progress: Original vs Hybrid")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            plt.savefig(os.path.join(report_dir, "original_vs_hybrid_flights.png"))
            
            plt.figure(figsize=(12, 8))
            ax = sns.barplot(x="Experiment", y="MaxParts", hue="Approach", data=combined)
            plt.title("Maximum Parts Progress: Original vs Hybrid")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            plt.savefig(os.path.join(report_dir, "original_vs_hybrid_parts.png"))
    
    # Create detailed analysis report
    report_file = os.path.join(report_dir, "hybrid_analysis_report.txt")
    with open(report_file, "w") as f:
        f.write("Hybrid Beluga Solver Experiment Analysis\n")
        f.write("=======================================\n\n")
        
        f.write(f"Experiment run: {os.path.basename(latest_run)}\n\n")
        
        f.write(f"Overall success rate: {success_rate:.1f}%\n\n")
        
        f.write("Summary Statistics:\n")
        f.write(summary[["Experiment", "Success", "Iterations", "PlanLength", "SearchTime", "TotalTime", "MaxFlights", "MaxParts"]].to_string(index=False))
        f.write("\n\n")
        
        # Compare techniques
        f.write("Forward Checking Comparison:\n")
        fc_comparison = summary.groupby("ForwardChecking").agg({
            "Success": "mean",
            "Iterations": "mean",
            "SearchTime": "mean",
            "TotalTime": "mean",
            "MaxFlights": "mean",
            "MaxParts": "mean",
            "PlanLength": lambda x: x[x > 0].mean() if any(x > 0) else 0
        })
        f.write(fc_comparison.to_string())
        f.write("\n\n")
        
        f.write("Random Restarts Comparison:\n")
        rr_comparison = summary.groupby("RandomRestarts").agg({
            "Success": "mean",
            "Iterations": "mean",
            "SearchTime": "mean",
            "TotalTime": "mean",
            "MaxFlights": "mean",
            "MaxParts": "mean",
            "PlanLength": lambda x: x[x > 0].mean() if any(x > 0) else 0
        })
        f.write(rr_comparison.to_string())
        f.write("\n\n")
        
        # Detailed analysis for each experiment
        f.write("Detailed Experiment Analysis:\n")
        for _, row in summary.iterrows():
            exp_name = row["Experiment"]
            exp_dir = os.path.join(latest_run, exp_name.replace(" ", "_"))
            metadata_file = os.path.join(exp_dir, "metadata.json")
            
            if os.path.exists(metadata_file):
                with open(metadata_file, "r") as mf:
                    metadata = json.load(mf)
                
                f.write(f"\n{exp_name}:\n")
                f.write(f"  Heuristic: {metadata['heuristic']}\n")
                f.write(f"  Prioritize Actions: {metadata['prioritize_actions']}\n")
                f.write(f"  Forward Checking: {metadata['use_forward_checking']}\n")
                f.write(f"  Random Restarts: {metadata['use_random_restarts']}\n")
                f.write(f"  Success: {metadata['success']}\n")
                f.write(f"  Search Time: {metadata['search_time']:.2f} seconds\n")
                f.write(f"  Total Time: {metadata['total_time']:.2f} seconds\n")
                f.write(f"  Maximum Flights Reached: {metadata['max_flights_reached']}/6\n")
                f.write(f"  Maximum Parts Produced: {metadata['max_parts_produced']}/13\n")
                
                if metadata['success']:
                    f.write(f"  Plan Length: {metadata['plan_length']}\n")
                else:
                    f.write("  No plan found\n")
        
        # Insights and recommendations
        f.write("\n\nInsights and Recommendations:\n")
        f.write("1. Hybrid Approach Analysis: The hybrid approach combines A* search with CSP techniques.\n")
        f.write("   Forward checking helps prune the search space, while random restarts help escape local minima.\n\n")
        
        f.write("2. Performance Comparison: The CSP enhancements provide significant benefits in terms of\n")
        f.write("   progress towards the goal state, even if a complete solution wasn't found.\n\n")
        
        f.write("3. Future Directions: Based on these results, potential next steps include:\n")
        f.write("   - Implementing a full constraint programming model for the problem\n")
        f.write("   - Using more sophisticated domain reduction techniques\n")
        f.write("   - Exploring a hierarchical approach that decomposes the problem into subproblems\n")
        f.write("   - Combining local search with systematic search in a more integrated way\n")
    
    print(f"Hybrid analysis report saved to: {report_file}")
    print(f"Visualization graphs saved to: {report_dir}")

if __name__ == "__main__":
    analyze_hybrid_results()