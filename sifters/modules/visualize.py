import matplotlib.pyplot as plt
import random

def visualize(data):
    num_groups = len(data)

    x = []
    y = []
    colors = []

    for group_index, group in enumerate(data):
        group_color = plt.cm.jet(random.random())  # Generate a color for the current group
        for sublist_index, sublist in enumerate(group):
            sublist_color = group_color  # Assign the same color to each sublist within the group
            for value in sublist:
                x.append(value)
                y.append(sublist_index + group_index * len(group))
                colors.append(sublist_color)  # Assign the color to each point within the sublist

    plt.scatter(x, y, color=colors)
    plt.yticks(range(len(data[0]) * num_groups), [idx // len(data[0]) for idx in range(len(data[0]) * num_groups)])
    plt.xlabel('Integer Value')
    plt.ylabel('List')
    plt.title('Scatter Plot')
    plt.show()