import matplotlib.pyplot as plt
from matplotlib.colors import CSS4_COLORS
from matplotlib import colors as mcolors
import numpy as np
from modules.Models import Flow_assignment
import random


# Function to calculate the luminance of a color
def get_luminance(color):
    rgb = mcolors.to_rgb(color)  # Convert hex to RGB values
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


# Filter out light colors by setting a luminance threshold
def filter_dark_colors(color_dict, threshold=0.7):
    dark_colors = {
        name: color for name, color in color_dict.items() if get_luminance(color) < threshold
    }
    return dark_colors


def result_plot(k: int, flow_assignments: list[Flow_assignment], max_capacity: int):
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    # fig1.autofmt_xdate()
    # fig2.autofmt_xdate()
    # Set time interval boundaries on the x-axis
    time_intervals = np.arange(1, k + 1)

    # Create a dictionary to track the capacity used in each time interval
    interval_capacity_used = {
        (i, direction): 0 for i in time_intervals for direction in ["DL", "UL"]
    }

    dark_css_colors = filter_dark_colors(CSS4_COLORS)
    css_colors = list(dark_css_colors.values())
    random.shuffle(css_colors)

    # Plot each flow as a bar in its assigned time interval
    for i, flow_assignment in enumerate(flow_assignments):
        serve_times = flow_assignment.fiveG_link_serve_time
        print(
            flow_assignment.flow.id,
            flow_assignment.serve_time,
            flow_assignment.fiveG_link_serve_time,
            flow_assignment.rb_usage,
        )
        for serve_time in serve_times:
            if serve_time == -1:
                continue
            flow = flow_assignment.flow
            payload_size = flow_assignment.rb_usage
            direction = flow_assignment.direction

            # Calculate the starting point of the flow in the time interval based on capacity used so far
            bottom_capacity = interval_capacity_used[serve_time, direction]

            bar_color = css_colors[i % len(css_colors)]
            # Plot the flow as a bar in the assigned time interval
            if direction == "DL":
                ax2.bar(
                    serve_time,
                    payload_size,
                    bottom=bottom_capacity,
                    color=bar_color,
                    label=f"Flow {flow.id}",
                )
            else:
                ax1.bar(
                    serve_time,
                    payload_size,
                    bottom=bottom_capacity,
                    color=bar_color,
                    label=f"Flow {flow.id}",
                )

            # Update the capacity used in this time interval
            interval_capacity_used[serve_time, direction] += payload_size

    # Plot the capacity limit for each time interval as a dashed line
    for i in time_intervals:
        ax1.plot(
            [i - 0.4, i + 0.4],
            [max_capacity, max_capacity],
            "r--",
            label="Capacity Limit" if i == 0 else "",
        )
        ax2.plot(
            [i - 0.4, i + 0.4],
            [max_capacity, max_capacity],
            "r--",
            label="Capacity Limit" if i == 0 else "",
        )

    # Adding labels and title
    ax1.set_xlabel("Time Interval")
    ax1.set_ylabel("Capacity Usage(# of RBs)")
    ax1.set_title("Flow Assignment to Time Intervals with Capacity Usage UL")
    ax1.set_xticks(time_intervals)
    ax1.set_ylim(0, max_capacity + 20)
    ax1.annotate(f"{max_capacity}", xy=(k + 0.3, max_capacity), color="red")
    handles1, labels1 = ax1.get_legend_handles_labels()
    unique1 = dict(zip(labels1, handles1))
    ax1.legend(unique1.values(), unique1.keys(), loc="upper left", bbox_to_anchor=(1, 1))

    ax2.set_xlabel("Time Interval")
    ax2.set_ylabel("Capacity Usage(# of RBs)")
    ax2.set_title("Flow Assignment to Time Intervals with Capacity Usage DL")
    ax2.set_xticks(time_intervals)
    ax2.set_ylim(0, max_capacity + 20)
    ax2.annotate(f"{max_capacity}", xy=(k + 0.3, max_capacity), color="red")
    handles2, labels2 = ax2.get_legend_handles_labels()
    unique2 = dict(zip(labels2, handles2))
    ax2.legend(unique2.values(), unique2.keys(), loc="upper left", bbox_to_anchor=(1, 1))

    # Show the plot
    plt.tight_layout()
    plt.show()
