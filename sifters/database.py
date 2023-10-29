import math


class Database:

    def __init__(self, mediator):

        self.connection = mediator.connection

        self.cursor = mediator.cursor

        self.grids_set = mediator.grids_set

        self.repeats = mediator.repeats

        self.period = mediator.period

        self.ticks_per_beat = mediator.ticks_per_beat

        self.scaling_factor = mediator.scaling_factor

        self.create_textures_table()

        self.create_notes_table()

        self.create_midi_messages_table()

    
    def create_textures_table(self):
        sql_command = f'''
        CREATE TABLE IF NOT EXISTS textures (
            texture_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )'''
        self.cursor.execute(sql_command)
        self.connection.commit()


    def create_notes_table(self):
        sql_command = '''
        CREATE TABLE IF NOT EXISTS notes (
            note_id INTEGER PRIMARY KEY,
            texture_id INTEGER,
            Start INTEGER,
            Velocity INTEGER,
            Note TEXT,
            Duration INTEGER,
            FOREIGN KEY (texture_id) REFERENCES textures(texture_id)
        )'''
        self.cursor.execute(sql_command)
        self.connection.commit()


    def create_midi_messages_table(self):
        sql_command = '''
        CREATE TABLE IF NOT EXISTS midi_messages (
            message_id INTEGER PRIMARY KEY,
            note_id INTEGER,
            message_type TEXT,
            time INTEGER,
            FOREIGN KEY (note_id) REFERENCES notes(note_id)
        )'''
        self.cursor.execute(sql_command)
        self.connection.commit()


    # def fetch_texture_names(self):
    #     self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('textures', 'notes', 'midi_messages')")
    #     return [row[0] for row in self.cursor.fetchall()]

    


    def fetch_columns(self, texture, exclude_columns_set={}):
        self.cursor.execute(f'PRAGMA table_info("{texture}")')
        return [row[1] for row in self.cursor.fetchall() if row[1] not in exclude_columns_set]
    

    def find_first_texture_id(self, texture):
        sql_query = f'SELECT texture_id FROM "{texture}" LIMIT 1' # Define the SQL query to retrieve the first texture_id value.
        self.cursor.execute(sql_query) # Execute the SQL query.
        result = self.cursor.fetchone() # Fetch the result (should be a single row with the first texture_id).

        if result: # Check if a result was found.
            return result[0]  # Extract the first texture_id value from the result
        else:
            return None  # Return None if no result was found
        
    def fetch_columns_by_texture_id(self, texture_id, exclude_columns_set={}):
        # Get the first row for the given texture_id
        self.cursor.execute(f'SELECT * FROM notes WHERE texture_id = ? LIMIT 1', (texture_id,))
        row = self.cursor.fetchone()

        # If there's a row, get its column names; otherwise, return an empty list
        if row:
            # Use the keys of the row (which are column names) and filter out the ones in the exclude set
            return [col for col in row.keys() if col not in exclude_columns_set]
        else:
            return []

        
        
    def find_texture_name_by_id(self, texture_id):
        """Fetch the texture name for a given texture_id."""
        self.cursor.execute("SELECT name FROM textures WHERE texture_id = ?", (texture_id,))
        result = self.cursor.fetchone()
        
        if result:
            return result[0]
        else:
            return None

    
    # def insert_texture(self, texture_id, texture_name):
    #     return f'INSERT INTO textures (texture_id, name) VALUES ({texture_id}, "{texture_name}");'

    def insert_texture(self, texture_name):
        # Insert the texture name and allow the database to auto-increment the texture_id
        return f'INSERT INTO textures (name) VALUES ("{texture_name}");'
    

    def insert_into_notes_command(self, texture_id, texture_table_names):
        commands = []
        # Given that texture_table_names holds the names of the tables which contain the notes
        # related to the specific texture, we will loop through these tables and generate
        # the insert commands.
        for texture_table_name in texture_table_names:
            cols = self.fetch_columns(texture_table_name)
            cols_string = ', '.join([f'"{col}"' for col in cols])
            
            # This command will insert data from each of the texture-specific tables into the main notes table.
            # Since we're working with the texture_id now, the INSERT command will also include this ID.
            sql_command = f'''
            INSERT INTO notes (texture_id, {cols_string})
            SELECT {texture_id}, {cols_string}
            FROM "{texture_table_name}";
            '''
            commands.append(sql_command)

        return "\n".join(commands)

    

    # def insert_into_notes_command(self, texture_id):
    #     # Prepare the SQL command to insert notes related to the specific texture_id
    #     # into the notes table.
    #     sql_command = f'''
    #     INSERT INTO notes (texture_id, [other_columns...])
    #     SELECT {texture_id}, [other_columns...]
    #     FROM notes
    #     WHERE texture_id = {texture_id};
    #     '''
    #     return sql_command

    
    # def insert_into_notes_command(self, texture_id):
    #     # Generate an SQL command to insert notes for a given texture_id into the notes table
    #     # This approach assumes the source data structure matches the destination notes table structure
    #     # If this isn't the case, you might need further transformations

    #     # The columns might be specific to each texture, or they might be standardized
    #     # For this example, I'll assume a standard set of columns, but you can adjust as needed
    #     columns = ['texture_id', 'Start', 'Velocity', 'Note', 'Duration']

    #     columns_string = ', '.join([f'"{col}"' for col in columns])

    #     # Generate the SQL command
    #     sql_command = f'INSERT INTO notes ({columns_string}) SELECT {columns_string} FROM notes WHERE texture_id = {texture_id};'

    #     return sql_command


    

    # def insert_into_notes_command(self, texture_table_names):        
    #     commands = []
    #     for texture_table_name in texture_table_names:
    #         cols = self.fetch_columns(texture_table_name)
    #         cols_string = ', '.join([f'"{col}"' for col in cols])
    #         sql_command = f'INSERT INTO notes ({cols_string}) SELECT {cols_string} FROM "{texture_table_name}";'
    #         commands.append(sql_command)

    #     return "\n".join(commands)
    

    def fetch_distinct_textures(self):
        self.cursor.execute("SELECT DISTINCT texture_id FROM notes")
        return [row[0] for row in self.cursor.fetchall()]


    def fetch_notes_for_texture(self, texture_id):
        self.cursor.execute("SELECT * FROM notes WHERE texture_id = ?", (texture_id,))
        return self.cursor.fetchall()


    def insert_midi_message(self, midi_message_data):
        sql_insert = '''
            INSERT INTO midi_messages (note_id, message_type, time, ...)
            VALUES (?, ?, ?, ...)
        '''
        self.cursor.execute(sql_insert, midi_message_data)
        self.connection.commit()


    def process_note_to_midi(self, note):
        midi_message_data = []
        print(note[1])
        return midi_message_data


    def generate_union_all_statements(self, texture_id, columns_string, duration_value, length_of_one_rep, repeat):
        accumulative_value = 0
        select_statements = []

        for _ in range(repeat):
            select_statements.append(f'''
            SELECT {columns_string}, 
            "Start" * {duration_value} + {accumulative_value} AS "Start",
            "Duration" * {duration_value} AS "Duration"
            FROM notes WHERE texture_id = {texture_id}''')
            accumulative_value += length_of_one_rep

        return " UNION ALL ".join(select_statements)

    # def generate_union_all_statements(self, texture, columns_string, duration_value, length_of_one_rep, repeat):
    #     accumulative_value = 0
    #     select_statements = []

    #     for _ in range(repeat):
    #         select_statements.append(f'''
    #         SELECT {columns_string}, 
    #         "Start" * {duration_value} + {accumulative_value} AS "Start",
    #         "Duration" * {duration_value} AS "Duration"
    #         FROM "{texture}"''')
    #         accumulative_value += length_of_one_rep
        
    #     return " UNION ALL ".join(select_statements)
    

    def generate_sql_for_duration_values(self, texture_id, columns_string):
        duration_values = [grid * self.scaling_factor for grid in self.grids_set]
        length_of_reps = [int(math.pow(self.period, 2) * duration) for duration in duration_values]

        table_commands = {}
        for duration_value, length_of_one_rep, repeat in zip(duration_values, length_of_reps, self.repeats):
            # Here we will name the table with the texture_id instead of the texture name.
            table_name = f"texture_{texture_id}_{duration_value}"
            table_commands[table_name] = self.generate_union_all_statements(texture_id, columns_string, duration_value, length_of_one_rep, repeat)

        return table_commands

    # def generate_sql_for_duration_values(self, texture, columns_string):
    #     duration_values = [grid * self.scaling_factor for grid in self.grids_set]
    #     length_of_reps = [int(math.pow(self.period, 2) * duration) for duration in duration_values]

    #     table_commands = {}
    #     for duration_value, length_of_one_rep, repeat in zip(duration_values, length_of_reps, self.repeats):
    #         table_name = f"{texture}_{duration_value}"
    #         table_commands[table_name] = self.generate_union_all_statements(texture, columns_string, duration_value, length_of_one_rep, repeat)
        
    #     return table_commands
    

    def generate_combined_commands(self, texture, duration_values):
        new_tables = [f'{texture}_{grid * self.scaling_factor}' for grid in duration_values]
        select_statements = [f'SELECT * FROM "{new_table}"' for new_table in new_tables]
        return f'''CREATE TABLE "{texture}_combined" AS 
                            {" UNION ".join(select_statements)};'''
    

    def create_temporary_texture_table(self, notes, texture_id):
        table_name = f"temp_texture_{texture_id}"
        columns = list(notes[0].keys())
        column_def = ", ".join([f'"{column}" TEXT' for column in columns])
        
        # Create table command
        create_table_command = f'''
        CREATE TABLE {table_name} (
            {column_def}
        );
        '''

        # Return the create table SQL command
        return create_table_command


    def insert_into_temp_texture_table(self, notes, texture_id):
        """Generate a SQL command to insert provided notes into a temporary table."""

        table_name = f"temp_texture_{texture_id}"

        # Extract columns from the first note (which is an sqlite3.Row object)
        columns = ', '.join(['"' + col + '"' for col in notes[0].keys()])

        print(columns)

        for note in notes:
            print(note[0])

        # # Generate a list of full insert commands with values directly embedded
        # insert_commands = [
        #     f'INSERT INTO {table_name} ({columns}) VALUES ({", ".join(map(repr, tuple(note)))});'
        #     for note in notes
        # ]

        # # Return the combined insert SQL commands
        # return "\n".join(insert_commands)
        return None


    

    def generate_grouped_commands(self, texture, columns):
        group_query_parts = [f'GROUP_CONCAT("{column}") as "{column}"' for column in columns]
        group_query_parts.append('GROUP_CONCAT("Duration") AS "Duration"')
        group_query_body = ', '.join(group_query_parts)
        return f'''
        CREATE TABLE "{texture}_grouped" AS
        SELECT Start, {group_query_body}
        FROM "{texture}_combined"
        GROUP BY Start;
        '''


    def generate_max_duration_command(self, texture):
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


    def generate_drop_duplicates_command(self, texture):
        return f'''
        CREATE TABLE temp_table AS
        SELECT DISTINCT * FROM "{texture}_max_duration";
        DROP TABLE "{texture}_max_duration";
        ALTER TABLE temp_table RENAME TO "{texture}_max_duration";
        '''


    def generate_create_end_table_command(self, texture):
        return f'''
        CREATE TABLE "{texture}_end_column" (
            Start INTEGER, 
            End INTEGER, 
            Duration INTEGER,
            Velocity INTEGER, 
            Note TEXT
        );
        '''


    def generate_insert_end_data_command(self, texture):
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


    def generate_add_pitch_column_command(self, texture):
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
    
    
    def generate_midi_messages_table_command(self, texture):
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

    def cleanup_database(self, texture_name):
        # Fetch names of all tables in the database
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = [row[0] for row in self.cursor.fetchall()]

        # List of tables you want to keep
        keep_tables = ['textures', 'notes', 'midi_messages']

        # Find tables that start with the texture name and are not in the keep list
        tables_to_drop = [table for table in all_tables if table.startswith(texture_name) and table not in keep_tables]

        # Generate DROP TABLE SQL statements for the tables to drop and concatenate them
        sql_commands_to_drop = '\n'.join([f'DROP TABLE IF EXISTS {table};' for table in tables_to_drop])

        return sql_commands_to_drop