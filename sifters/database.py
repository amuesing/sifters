import datetime
import math
import sqlite3


class Database:
    
    
    def __init__(self, mediator, use_timestamp=False):
        if use_timestamp:
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            db_name = f'data/db/{self.__class__.__name__}_{timestamp}.db'
        else:
            db_name = f'data/db/{self.__class__.__name__}.db'

        self.connection = sqlite3.connect(db_name)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        
        self.normalized_grids = mediator.normalized_grids
        self.grids_set = mediator.grids_set
        self.repeats = mediator.repeats
        self.period = mediator.period
        self.ticks_per_beat = mediator.ticks_per_beat
        self.scaling_factor = mediator.scaling_factor
        
    
    def clear_database(self):
        # Get a list of all tables in the database
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.cursor.fetchall()

        # Drop each table
        for table in tables:
            self.cursor.execute(f"DROP TABLE IF EXISTS {table['name']}")

        # Commit the changes to make them permanent
        self.connection.commit()

    
    def create_table(self, table_name, columns):
        sql_command = f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                {columns}
            )'''
        self.cursor.execute(sql_command)
        self.connection.commit()
        
        
    def create_textures_table(self):
        columns = '''
            Name TEXT,
            GridID INTEGER PRIMARY KEY
        '''
        self.create_table('textures', columns)
        
        
    def create_grids_table(self):
        columns = '''
            Numerator INTEGER,
            Denominator INTEGER,
            GridID INTEGER PRIMARY KEY
        '''
        self.create_table('grids', columns)

        # Insert fractions into the "grids" table
        for grid_id, fraction in enumerate(self.grids_set, start=1):
            self.cursor.execute('INSERT INTO grids (Numerator, Denominator, GridID) VALUES (?, ?, ?)',
                                (fraction.numerator, fraction.denominator, grid_id))

        self.connection.commit()


    def create_notes_table(self):
        columns = '''
            Start INTEGER,
            Velocity INTEGER,
            Note INTEGER,
            Duration INTEGER,
            NoteID INTEGER PRIMARY KEY,
            GridID INTEGER
        '''
        
        self.create_table('notes', columns)


    def create_messages_table(self):
        columns = '''
            Start INTEGER,
            End INTEGER,
            Velocity INTEGER,
            Note INTEGER,
            Message TEXT,
            Time INTEGER,
            MessageID INTEGER PRIMARY KEY,
            NoteID INTEGER,
            GridID INTEGER
        '''
        
        self.create_table('messages', columns)

        
    def insert_dataframe_into_database(self, table_name, dataframe):
        dataframe.to_sql(name=f'{table_name}', con=self.connection, if_exists='append', index=False)


    def fetch_columns_by_table_name(self, table_name, exclude_columns={}):
        self.cursor.execute(f'SELECT * FROM "{table_name}"')
        row = self.cursor.fetchone()
        columns = [col for col in row.keys() if col not in exclude_columns]

        return columns
    

    def generate_union_all_statements(self, columns_string, duration_value, length_of_one_rep, repeat):
        accumulative_value = 0
        select_statements = []

        for _ in range(repeat):
            select_statements.append(f'''
            SELECT {columns_string}, 
            "Start" * {duration_value} + {accumulative_value} AS "Start",
            "Duration" * {duration_value} AS "Duration"
            FROM notes''')
            accumulative_value += length_of_one_rep

        return " UNION ALL ".join(select_statements)
    
    
    def generate_duration_commands(self, columns_list):
        columns_string = ', '.join(columns_list)

        # Fetch fractions and GridIDs from the "grids" table
        self.cursor.execute('SELECT * FROM grids')
        fractions_and_grid_ids = self.cursor.fetchall()

        # Generate duration values based on fractions
        duration_commands = {}
        for row in fractions_and_grid_ids:
            fraction = row['Numerator'] / row['Denominator']
            grid_id = row['GridID']

            repeat_index = grid_id - 1
            repeat = self.repeats[repeat_index] if self.normalized_grids and 0 <= repeat_index < len(self.repeats) else 1
            duration_value = fraction * self.scaling_factor
            length_of_one_rep = int(math.pow(self.period, 2) * duration_value)
            table_name = f'grid_{grid_id}'
            duration_commands[table_name] = self.generate_union_all_statements(f'{columns_string}, {grid_id} AS "GridID"', duration_value, length_of_one_rep, repeat)

        return duration_commands


    def insert_into_notes_command(self, table_names):
        commands = []

        for table_name in table_names:
            cols = self.fetch_columns_by_table_name(table_name)
            cols_string = ', '.join([f'"{col}"' for col in cols])

            # Insert data from each table into the notes table
            sql_command = f'INSERT INTO notes ({cols_string}) SELECT {cols_string} FROM "{table_name}";'
            commands.append(sql_command)

        return "\n".join(commands)
    
    
    def select_distinct_grids(self):
        self.cursor.execute('SELECT GridID FROM grids')
        grid_ids = [row['GridID'] for row in self.cursor.fetchall()]
        
        return grid_ids
    
    
    def generate_max_duration_commands(self, grid_id):
        max_duration_command = f'''
        CREATE TEMPORARY TABLE max_duration_{grid_id} AS
        WITH max_durations AS (
            SELECT Start, MAX(Duration) as MaxDuration
            FROM notes
            WHERE GridID = {grid_id}
            GROUP BY Start
        )
        SELECT c.Start, c.Velocity, c.Note, m.MaxDuration as Duration, c.NoteID, c.GridID
        FROM notes c
        LEFT JOIN max_durations m ON c.Start = m.Start
        WHERE GridID = {grid_id};
        '''
        
        return max_duration_command


    def preprocess_max_duration(self, grid_id):
        preprocess_command = f'''
            CREATE TEMPORARY TABLE preprocess_max_duration_{grid_id} AS
            WITH OrderedMaxDuration AS (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY Start ORDER BY Duration DESC) AS row_num
                FROM max_duration_{grid_id}
            )
            SELECT Start, Velocity, Note, Duration, NoteID, GridID
            FROM OrderedMaxDuration
            WHERE row_num = 1;

            DELETE FROM max_duration_{grid_id};

            INSERT INTO max_duration_{grid_id} SELECT * FROM preprocess_max_duration_{grid_id};
        '''
        
        return preprocess_command


    def generate_end_column_command(self, grid_id):
        create_table_command = f'''
            CREATE TEMPORARY TABLE end_column_{grid_id} (
                Start INTEGER, 
                End INTEGER, 
                Duration INTEGER,
                Velocity INTEGER, 
                Note INTEGER,
                NoteID INTEGER,
                GridID INTEGER
            );
        '''
        
        return create_table_command
    
    
    def insert_end_column_data(self, grid_id):
        insert_data_command = f'''
            INSERT INTO end_column_{grid_id}
            SELECT
                m.Start,
                MIN(m.Start + m.Duration, LEAD(m.Start, 1, m.Start + m.Duration) OVER (ORDER BY m.Start)) AS End,
                m.Duration,
                m.Velocity,
                m.Note,
                m.NoteID,
                m.GridID
            FROM max_duration_{grid_id} m;
        '''

        return insert_data_command
    
    
    def generate_message_column_command(self, grid_id):
        create_table_command = f'''
            CREATE TEMPORARY TABLE message_column_{grid_id} (
                Start INTEGER, 
                End INTEGER, 
                Duration INTEGER,
                Velocity INTEGER, 
                Note INTEGER,
                Message TEXT,
                NoteID INTEGER,
                GridID INTEGER
            );
        '''
        
        return create_table_command
    

    def insert_message_column_data(self, grid_id):
        insert_command = f'''
            WITH RestRows AS (
                SELECT
                    m.Start,
                    m.End,
                    m.Duration,
                    m.Velocity,
                    m.Note,
                    'note_on' AS Message,
                    m.NoteID,
                    m.GridID
                FROM (
                    SELECT
                        m.Start,
                        LEAD(m.Start) OVER (ORDER BY m.Start) AS lead_start,
                        m.End,
                        m.Duration,
                        m.Velocity,
                        m.Note,
                        m.NoteID,
                        m.GridID
                    FROM end_column_{grid_id} m
                ) m
                WHERE m.lead_start > m.End
            )
            INSERT INTO message_column_{grid_id}
            SELECT
                CASE WHEN lead_start > m.End THEN m.End ELSE m.Start END AS Start,
                COALESCE(lead_start, m.End) AS End,
                COALESCE(lead_start, m.End) - CASE WHEN lead_start > m.End THEN m.End ELSE m.Start END AS Duration,
                m.Velocity,
                m.Note,
                CASE WHEN lead_start > m.End THEN 'note_off' ELSE 'note_on' END AS Message,
                m.NoteID,
                m.GridID
            FROM (
                SELECT
                    m.Start,
                    LEAD(m.Start) OVER (ORDER BY m.Start) AS lead_start,
                    m.End,
                    m.Velocity,
                    m.Note,
                    m.NoteID,
                    m.GridID
                FROM end_column_{grid_id} m
            ) m
            UNION ALL
            SELECT * FROM RestRows
            ORDER BY Start;
        '''

        return insert_command


    def create_temporary_midi_messages_table(self, grid_id):
        return f'''
            CREATE TEMPORARY TABLE midi_messages_{grid_id} AS
            SELECT  
                Start,
                End,
                Velocity,
                Note,
                Message,
                CASE 
                    WHEN Message = 'note_on' AND ROW_NUMBER() OVER (ORDER BY Start ASC) = 1 AND Start != 0 THEN ROUND(Start * {self.ticks_per_beat})
                    WHEN Message = 'note_off' THEN ROUND((End - Start) * {self.ticks_per_beat})  -- Calculate Time as (End - Start) for 'note_off'
                    ELSE 0 
                END AS Time,
                NoteID,
                GridID
            FROM message_column_{grid_id};
        '''

        
    def append_note_off_message(self, grid_id):
        return f'''
            INSERT INTO midi_messages_{grid_id} (Start, End, Velocity, Note, Message, Time, NoteID, GridID)
            SELECT 
                Start, End, Velocity, Note,
                'note_off' AS Message,
                (End - Start) * {self.ticks_per_beat} AS Time,
                NoteID,
                GridID
            FROM midi_messages_{grid_id} AS t
            WHERE Message = 'note_on';
        '''


    def order_midi_messages_by_start(self, grid_id):
        return f'''
            CREATE TEMPORARY TABLE midi_messages_ordered_{grid_id} AS
            SELECT
                Start,
                End,
                Velocity,
                Note,
                Message,
                Time,
                NoteID,
                GridID
            FROM midi_messages_{grid_id}
            ORDER BY Start;
        '''


    def insert_into_messages_table(self, grid_id):
        return f'''
            INSERT INTO messages (Start, End, Velocity, Note, Message, Time, NoteID, GridID)
            SELECT Start, End, Velocity, Note, Message, Time, NoteID, GridID
            FROM midi_messages_ordered_{grid_id}
            ORDER BY Start ASC;
        '''