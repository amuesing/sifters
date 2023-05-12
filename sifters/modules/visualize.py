import matplotlib.pyplot

def create_midi_scatter_with_lines(dataframe):
    # create the scatter plot
    fig, ax = matplotlib.pyplot.subplots()
    ax.scatter(dataframe['Start'], dataframe['MIDI'], s=20, label='MIDI')

    # plot lines connecting start and end values
    for i, row in dataframe.iterrows():
        ax.plot([row['Start'], row['End']], [row['MIDI'], row['MIDI']], 'k-', linewidth=0.5)
        ax.plot([row['End']], [row['MIDI']], 'k|', markersize=10)

        # add text labels for MIDI values
        ax.text(row['Start'], row['MIDI'], str(row['MIDI']), fontsize=6)

    # add labels and title
    ax.set_xlabel('Start')
    ax.set_ylabel('MIDI')
    ax.set_title('MIDI vs. Start')

    # show the plot
    matplotlib.pyplot.show()