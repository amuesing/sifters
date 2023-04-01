import pandas

class Utility:
    def grouped_by_offset_and_midi(dataframe):
        grouped_by_offset = dataframe.groupby('Offset')['MIDI'].apply(lambda x: sorted([i for i in x])).reset_index()
        grouped_by_offset['MIDI'] = grouped_by_offset['MIDI'].apply(tuple)
        return grouped_by_offset.groupby('MIDI')['Start'].agg(lambda x: list(x)).reset_index()
    
    def aggregate_rows(dataframe):
        groups = dataframe.groupby('MIDI')
        result = pandas.DataFrame(columns=['Start', 'End', 'MIDI'])
        for name, group in groups:
            start = group['Start'].iloc[0]
            end = group['End'].iloc[-1] if group['End'].iloc[-1] is not pandas.NA else group['Start'].iloc[-1] + 1
            result = result.append({'Start': start, 'End': end, 'MIDI': name}, ignore_index=True)
        return result
    
    @staticmethod
    def save_as_csv(dataframe, filename):
        dataframe.sort_values(by = 'Start').to_csv(f'sifters/.{filename}.csv', index=False)
        
    @staticmethod
    def save_as_midi(pretty_midi_obj, filename):
        pretty_midi_obj.write(f'sifters/.{filename}.mid')