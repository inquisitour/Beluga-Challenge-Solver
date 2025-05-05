import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Get the latest results directory
results_dir = "improved_experiment_results"
run_dirs = [os.path.join(results_dir, d) for d in os.listdir(results_dir) if d.startswith("run_")]

if not run_dirs:
    print("No experiment results found. Please run improved_run_experiments.py first.")
    exit(1)

latest_run = max(run_dirs, key=os.path.getmtime)

print(f"Analyzing improved results from: {latest_run}")

# Read the summary file
summary_file = os.path.join(latest_run, "summary.csv")
summary = pd.read_csv(summary_file)

# Calculate success rate
success_rate = summary["Success"].mean() * 100
print(f"Overall success rate: {success_rate:.1f}%")

# Print summary statistics
print("\nSummary Statistics:")
print(summary[["Experiment", "Success", "Iterations", "PlanLength", "SearchTime", "TotalTime"]])

# Create report directory
report_dir = os.path.join(latest_run, "analysis")
os.makedirs(report_dir, exist_ok=True)

# Plot iterations comparison
plt.figure(figsize=(10, 6))
sns.barplot(x="Experiment", y="Iterations", data=summary, hue="Success")
plt.title("Number of Iterations by Experiment")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(os.path.join(report_dir, "iterations_comparison.png"))

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

# Analyze detailed experiment results
experiment_details = []
for exp_name in summary["Experiment"]:
    exp_dir = os.path.join(latest_run, exp_name.replace(" ", "_"))
    metadata_file = os.path.join(exp_dir, "metadata.json")
    progress_file = os.path.join(exp_dir, "progress_data.json")
    
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
            experiment_details.append(metadata)
    
    # Plot progress over time if progress data exists
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            progress_data = json.load(f)
            
        # Convert to DataFrame
        progress_df = pd.DataFrame(progress_data)
        
        # Plot flights progress
        plt.figure(figsize=(12, 6))
        plt.plot(progress_df["iteration"], progress_df["flights"], marker='o', linestyle='-', markersize=2)
        plt.title(f"{exp_name}: Flights Processed Over Iterations")
        plt.xlabel("Iterations")
        plt.ylabel("Flights Processed")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(report_dir, f"{exp_name.replace(' ', '_')}_flights_progress.png"))
        
        # Plot parts progress
        plt.figure(figsize=(12, 6))
        plt.plot(progress_df["iteration"], progress_df["parts"], marker='o', linestyle='-', markersize=2)
        plt.title(f"{exp_name}: Parts Produced Over Iterations")
        plt.xlabel("Iterations")
        plt.ylabel("Parts Produced")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(report_dir, f"{exp_name.replace(' ', '_')}_parts_progress.png"))
        
        # Combined progress heatmap
        if len(progress_df) > 0:
            # Create a 2D histogram
            flight_bins = np.arange(0, 7)  # 0-6 flights
            part_bins = np.arange(0, 14)   # 0-13 parts
            
            hist, xedges, yedges = np.histogram2d(
                progress_df["flights"], 
                progress_df["parts"], 
                bins=[flight_bins, part_bins]
            )
            
            # Plot heatmap
            plt.figure(figsize=(10, 8))
            plt.imshow(hist.T, origin='lower', aspect='auto', 
                    extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
                    cmap='viridis')
            plt.colorbar(label='Frequency')
            plt.title(f"{exp_name}: State Space Exploration")
            plt.xlabel("Flights Processed")
            plt.ylabel("Parts Produced")
            plt.xticks(np.arange(0, 7))
            plt.yticks(np.arange(0, 14))
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(os.path.join(report_dir, f"{exp_name.replace(' ', '_')}_state_heatmap.png"))

# Create detailed analysis report
report_file = os.path.join(report_dir, "improved_analysis_report.txt")
with open(report_file, "w") as f:
    f.write("Improved Beluga Solver Experiment Analysis\n")
    f.write("========================================\n\n")
    
    f.write(f"Experiment run: {os.path.basename(latest_run)}\n\n")
    
    f.write(f"Overall success rate: {success_rate:.1f}%\n\n")
    
    f.write("Summary Statistics:\n")
    f.write(summary[["Experiment", "Success", "Iterations", "PlanLength", "SearchTime", "TotalTime"]].to_string(index=False))
    f.write("\n\n")
    
    # Compare heuristics
    f.write("Heuristic Comparison:\n")
    heuristic_comparison = summary.groupby("Heuristic").agg({
        "Success": "mean",
        "Iterations": "mean",
        "SearchTime": "mean",
        "TotalTime": "mean",
        "PlanLength": lambda x: x[x > 0].mean() if any(x > 0) else 0
    })
    f.write(heuristic_comparison.to_string())
    f.write("\n\n")
    
    # Compare action prioritization
    f.write("Action Prioritization Comparison:\n")
    prioritize_comparison = summary.groupby("Prioritize").agg({
        "Success": "mean",
        "Iterations": "mean",
        "SearchTime": "mean",
        "TotalTime": "mean",
        "PlanLength": lambda x: x[x > 0].mean() if any(x > 0) else 0
    })
    f.write(prioritize_comparison.to_string())
    f.write("\n\n")
    
    # Detailed analysis for each experiment
    f.write("Detailed Experiment Analysis:\n")
    for metadata in experiment_details:
        f.write(f"\n{metadata['name']}:\n")
        f.write(f"  Heuristic: {metadata['heuristic']}\n")
        f.write(f"  Prioritize Actions: {metadata['prioritize_actions']}\n")
        f.write(f"  Success: {metadata['success']}\n")
        f.write(f"  Iterations: {metadata['iterations']}\n")
        f.write(f"  Search Time: {metadata['search_time']:.2f} seconds\n")
        f.write(f"  Total Time: {metadata['total_time']:.2f} seconds\n")
        
        if "max_flights_reached" in metadata:
            f.write(f"  Maximum Flights Reached: {metadata['max_flights_reached']}/6\n")
        if "max_parts_produced" in metadata:
            f.write(f"  Maximum Parts Produced: {metadata['max_parts_produced']}/13\n")
        
        if metadata['success']:
            f.write(f"  Plan Length: {metadata['plan_length']}\n")
        else:
            f.write("  No plan found\n")
    
    # Insights and recommendations
    f.write("\n\nInsights and Recommendations:\n")
    f.write("1. Progress Analysis: The experiments show different patterns in state space exploration.\n")
    f.write("   Each variant tends to focus on different aspects of the problem (flights vs. parts).\n\n")
    
    f.write("2. Performance Comparison: The extended iterations allow for deeper exploration of the\n")
    f.write("   state space, potentially reaching states closer to the goal.\n\n")
    
    f.write("3. Future Improvements: Based on these results, potential enhancements include:\n")
    f.write("   - Further increasing iterations for the most promising variant\n")
    f.write("   - Implementing a more sophisticated heuristic that balances flight and part processing\n")
    f.write("   - Developing a hierarchical approach that decomposes the problem into subproblems\n")

print(f"Improved analysis report saved to: {report_file}")
print(f"Visualization graphs saved to: {report_dir}")