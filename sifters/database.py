import math


class Database:

    def __init__(self, mediator):

        self.cursor = mediator.cursor

        self.grids_set = mediator.grids_set

        self.repeats = mediator.repeats

        self.period = mediator.period

        self.ticks_per_beat = mediator.ticks_per_beat

        self.scaling_factor = mediator.scaling_factor


    def _fetch_texture_names(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in self.cursor.fetchall()]


    def _fetch_columns(self, texture):
        exclude_columns_set = {'Start', 'Duration'}
        self.cursor.execute(f'PRAGMA table_info("{texture}")')
        return [row[1] for row in self.cursor.fetchall() if row[1] not in exclude_columns_set]


    def _generate_union_all_statements(self, texture, columns_string, duration_value, length_of_one_rep, repeat):
        accumulative_value = 0
        select_statements = []

        for _ in range(repeat):
            select_statements.append(f'''
            SELECT {columns_string}, 
            "Start" * {duration_value} + {accumulative_value} AS "Start",
            "Duration" * {duration_value} AS "Duration"
            FROM "{texture}"''')
            accumulative_value += length_of_one_rep
        
        return " UNION ALL ".join(select_statements)
    

    def _generate_sql_for_duration_values(self, texture, columns_string):
        duration_values = [grid * self.scaling_factor for grid in self.grids_set]
        length_of_reps = [int(math.pow(self.period, 2) * duration) for duration in duration_values]

        table_commands = {}
        for duration_value, length_of_one_rep, repeat in zip(duration_values, length_of_reps, self.repeats):
            table_name = f"{texture}_{duration_value}"
            table_commands[table_name] = self._generate_union_all_statements(texture, columns_string, duration_value, length_of_one_rep, repeat)
        
        return table_commands
    

    def _generate_combined_commands(self, texture, duration_values):
        new_tables = [f'{texture}_{grid * self.scaling_factor}' for grid in duration_values]
        select_statements = [f'SELECT * FROM "{new_table}"' for new_table in new_tables]
        return f'''CREATE TABLE "{texture}_combined" AS 
                            {" UNION ".join(select_statements)};'''
    

    def _generate_grouped_commands(self, texture, columns):
        group_query_parts = [f'GROUP_CONCAT("{column}") as "{column}"' for column in columns]
        group_query_parts.append('GROUP_CONCAT("Duration") AS "Duration"')
        group_query_body = ', '.join(group_query_parts)
        return f'''
        CREATE TABLE "{texture}_grouped" AS
        SELECT Start, {group_query_body}
        FROM "{texture}_combined"
        GROUP BY Start;
        '''


    def _generate_max_duration_command(self, texture):
        return f'''
        CREATE TABLE "{texture}_max_duration" AS
        WITH max_durations AS (
            SELECT Start, MAX(Duration) as MaxDuration
            FROM "{texture}_combined"
            GROUP BY Start
        )
        SELECT c.Start, c.Velocity, c.Note, m.MaxDuration as Duration
        FROM "{texture}_combined" c
        LEFT JOIN max_durations m ON c.Start = m.Start;
        '''


    def _generate_drop_duplicates_command(self, texture):
        return f'''
        CREATE TABLE temp_table AS
        SELECT DISTINCT * FROM "{texture}_max_duration";
        DROP TABLE "{texture}_max_duration";
        ALTER TABLE temp_table RENAME TO "{texture}_max_duration";
        '''


    def _generate_create_end_table_command(self, texture):
        return f'''
        CREATE TABLE "{texture}_end_column" (
            Start INTEGER, 
            End INTEGER, 
            Duration INTEGER,
            Velocity INTEGER, 
            Note TEXT
        );
        '''


    def _generate_insert_end_data_command(self, texture):
        return f'''
        WITH ModifiedDurations AS (
            SELECT 
                Start,
                Velocity,
                Note,
                Duration as ModifiedDuration
            FROM "{texture}_max_duration"
        ),
        DistinctEnds AS (
            SELECT
                Start,
                COALESCE(LEAD(Start, 1) OVER(ORDER BY Start), Start + ModifiedDuration) AS End
            FROM (SELECT DISTINCT Start, ModifiedDuration FROM ModifiedDurations) as distinct_starts
        )
        INSERT INTO "{texture}_end_column"
        SELECT 
            m.Start,
            d.End,
            m.ModifiedDuration,
            m.Velocity,
            m.Note
        FROM ModifiedDurations m
        JOIN DistinctEnds d ON m.Start = d.Start;
        '''


    def _generate_add_pitch_column_command(self, texture):
        return f'''
        CREATE TABLE "{texture}_base" AS 
        SELECT 
            Start,
            End,
            Velocity,
            CAST(Note AS INTEGER) AS Note,
            CAST((Note - CAST(Note AS INTEGER)) * 4095 AS INTEGER) AS Pitch
        FROM "{texture}_end_column";
        '''
    
    
    def _generate_midi_messages_table_command(self, texture):
        return f'''
            -- [1] Create the initial MIDI messages table:
            CREATE TABLE "{texture}_midi_messages_temp" AS
            SELECT 
                *,
                'note_on' AS Message,
                CASE 
                    WHEN ROW_NUMBER() OVER (ORDER BY Start ASC) = 1 AND Start != 0 THEN ROUND(Start * {self.ticks_per_beat})
                    ELSE 0 
                END AS Time
            FROM "{texture}_base";

            -- [2.1] Create a table of rows meeting the delta condition (generating rests):
            CREATE TABLE "{texture}_midi_rests" AS
            SELECT 
                a.*
            FROM "{texture}_midi_messages_temp" AS a
            JOIN (
                SELECT 
                    Start,
                    LAG(End) OVER (ORDER BY Start ASC) AS PreviousEnd,
                    LAG(Start) OVER (ORDER BY Start ASC) AS PreviousStart
                FROM "{texture}_midi_messages_temp"
            ) AS t
            ON a.Start = t.Start
            WHERE 
                a.Start != t.PreviousEnd 
                AND a.Start != t.PreviousStart;

            -- [2.2] Update the Time column in the main table based on delta condition:
            UPDATE "{texture}_midi_messages_temp"
            SET Time = (
                SELECT COALESCE("{texture}_midi_messages_temp".Start - t.PreviousEnd, 0)
                FROM (
                    SELECT 
                        Start,
                        LAG(End) OVER (ORDER BY Start ASC) AS PreviousEnd
                    FROM "{texture}_midi_messages_temp"
                ) AS t
                WHERE 
                    "{texture}_midi_messages_temp".Start = t.Start
            )
            WHERE EXISTS (
                SELECT 1
                FROM (
                    SELECT 
                        Start,
                        LAG(End) OVER (ORDER BY Start ASC) AS PreviousEnd,
                        LAG(Start) OVER (ORDER BY Start ASC) AS PreviousStart
                    FROM "{texture}_midi_messages_temp"
                ) AS t_sub
                WHERE 
                    "{texture}_midi_messages_temp".Start = t_sub.Start 
                    AND "{texture}_midi_messages_temp".Start != t_sub.PreviousEnd
                    AND "{texture}_midi_messages_temp".Start != t_sub.PreviousStart
            );

            -- [3] Append rows for 'pitchwheel' and 'note_off' events:
            INSERT INTO "{texture}_midi_messages_temp" (Start, End, Velocity, Note, Pitch, Message, Time)
            SELECT 
                Start, End, Velocity, Note, Pitch,
                'pitchwheel' AS Message,
                0 AS Time
            FROM "{texture}_midi_messages_temp"
            WHERE Message = 'note_on' AND Pitch != 0.0;

            INSERT INTO "{texture}_midi_messages_temp" (Start, End, Velocity, Note, Pitch, Message, Time)
            SELECT 
                Start, End, Velocity, Note, Pitch,
                'note_off' AS Message,
                (End - Start) * {self.ticks_per_beat} AS Time
            FROM "{texture}_midi_messages_temp"
            WHERE Message = 'note_on';

            -- [4] Organize the MIDI messages by 'Start' time and store in a new table:
            CREATE TABLE "{texture}_midi_messages" AS
            SELECT * FROM "{texture}_midi_messages_temp"
            ORDER BY Start ASC;

            -- [5] Cleanup: Drop the temporary table to free up resources:
            DROP TABLE "{texture}_midi_messages_temp";
        '''


    def _generate_cleanup_commands(self, texture):
        temporary_tables = [
            f'"{texture}_combined"',
            f'"{texture}_max_duration"',
            f'"{texture}_end_column"'
        ]
        return [f'DROP TABLE IF EXISTS {table};' for table in temporary_tables]