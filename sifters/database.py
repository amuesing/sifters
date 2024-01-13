import datetime
import math
import sqlite3


class Database:
    
    
    def __init__(self, mediator):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.connection = sqlite3.connect(f'data/db/.{self.__class__.__name__}_{timestamp}.db')
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

        self.grids_set = mediator.grids_set
        self.repeats = mediator.repeats
        self.period = mediator.period
        self.ticks_per_beat = mediator.ticks_per_beat
        self.scaling_factor = mediator.scaling_factor

    
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
            TextureID INTEGER PRIMARY KEY
        '''
        self.create_table('textures', columns)


    def create_notes_table(self):
        columns = '''
            Start INTEGER,
            Velocity INTEGER,
            Note TEXT,
            Duration INTEGER,
            NoteID INTEGER PRIMARY KEY,
            TextureID INTEGER
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
            TextureID INTEGER
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
        duration_values = [grid * self.scaling_factor for grid in self.grids_set]
        length_of_reps = [int(math.pow(self.period, 2) * duration) for duration in duration_values]

        table_commands = {}
        for duration_value, length_of_one_rep, repeat in zip(duration_values, length_of_reps, self.repeats):
            table_name = f"duration_{duration_value}"
            table_commands[table_name] = self.generate_union_all_statements(columns_string, duration_value, length_of_one_rep, repeat)

        return table_commands


    def insert_into_notes_command(self, table_names):
        commands = []

        for table_name in table_names:
            cols = self.fetch_columns_by_table_name(table_name)
            cols_string = ', '.join([f'"{col}"' for col in cols])

            # Insert data from each table into the notes table
            sql_command = f'INSERT INTO notes ({cols_string}) SELECT {cols_string} FROM "{table_name}";'
            commands.append(sql_command)

        return "\n".join(commands)


    def generate_max_duration_command(self):
        max_duration_command =  '''
        CREATE TEMPORARY TABLE max_duration AS
        WITH max_durations AS (
            SELECT Start, MAX(Duration) as MaxDuration
            FROM notes
            GROUP BY Start
        )
        SELECT c.Start, c.Velocity, c.Note, m.MaxDuration as Duration, c.NoteID, c.TextureID
        FROM notes c
        LEFT JOIN max_durations m ON c.Start = m.Start;
        '''
        
        return max_duration_command


    def preprocess_max_duration(self):
        preprocess_command = '''
            CREATE TEMPORARY TABLE preprocess_max_duration AS
            WITH OrderedMaxDuration AS (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY Start ORDER BY Duration DESC) AS row_num
                FROM max_duration
            )
            SELECT Start, Velocity, Note, Duration, NoteID, TextureID
            FROM OrderedMaxDuration
            WHERE row_num = 1;

            DELETE FROM max_duration;

            INSERT INTO max_duration SELECT * FROM preprocess_max_duration;
        '''
        
        return preprocess_command


    def generate_end_column_command(self):
        create_table_command = '''
            CREATE TEMPORARY TABLE end_column (
                Start INTEGER, 
                End INTEGER, 
                Duration INTEGER,
                Velocity INTEGER, 
                Note INTEGER,
                NoteID INTEGER,
                TextureID INTEGER
            );
        '''
        
        return create_table_command
    
    
    def insert_end_column_data(self):
        insert_data_command = '''
            INSERT INTO end_column
            SELECT
                m.Start,
                MIN(m.Start + m.Duration, LEAD(m.Start, 1, m.Start + m.Duration) OVER (ORDER BY m.Start)) AS End,
                m.Duration,
                m.Velocity,
                m.Note,
                m.NoteID,
                m.TextureID
            FROM max_duration m;
        '''

        return insert_data_command
    
    
    def generate_message_column_command(self):
        create_table_command = '''
            CREATE TEMPORARY TABLE message_column (
                Start INTEGER, 
                End INTEGER, 
                Duration INTEGER,
                Velocity INTEGER, 
                Note INTEGER,
                Message TEXT,
                NoteID INTEGER,
                TextureID INTEGER
            );
        '''
        
        return create_table_command
    

    def insert_message_column_data(self):
        insert_command = '''
            WITH RestRows AS (
                SELECT
                    m.Start,
                    m.End,
                    m.Duration,
                    m.Velocity,
                    m.Note,
                    'note_on' AS Message,
                    m.NoteID,
                    m.TextureID
                FROM (
                    SELECT
                        m.Start,
                        LEAD(m.Start) OVER (ORDER BY m.Start) AS lead_start,
                        m.End,
                        m.Duration,
                        m.Velocity,
                        m.Note,
                        m.NoteID,
                        m.TextureID
                    FROM end_column m
                ) m
                WHERE m.lead_start > m.End
            )
            INSERT INTO message_column
            SELECT
                CASE WHEN lead_start > m.End THEN m.End ELSE m.Start END AS Start,
                COALESCE(lead_start, m.End) AS End,
                COALESCE(lead_start, m.End) - CASE WHEN lead_start > m.End THEN m.End ELSE m.Start END AS Duration,
                m.Velocity,
                m.Note,
                CASE WHEN lead_start > m.End THEN 'note_off' ELSE 'note_on' END AS Message,
                m.NoteID,
                m.TextureID
            FROM (
                SELECT
                    m.Start,
                    LEAD(m.Start) OVER (ORDER BY m.Start) AS lead_start,
                    m.End,
                    m.Velocity,
                    m.Note,
                    m.NoteID,
                    m.TextureID
                FROM end_column m
            ) m
            UNION ALL
            SELECT * FROM RestRows
            ORDER BY Start;
        '''

        return insert_command


    def create_temporary_midi_messages_table(self):
        return f'''
            CREATE TEMPORARY TABLE "midi_messages" AS
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
                TextureID
            FROM "message_column";
        '''

        
    def append_note_off_message(self):
        return f'''
            INSERT INTO "midi_messages" (Start, End, Velocity, Note, Message, Time, NoteID, TextureID)
            SELECT 
                Start, End, Velocity, Note,
                'note_off' AS Message,
                (End - Start) * {self.ticks_per_beat} AS Time,
                NoteID,
                TextureID
            FROM "midi_messages" AS t
            WHERE Message = 'note_on';
        '''


    def order_midi_messages_by_start(self):
        return '''
            CREATE TEMPORARY TABLE "midi_messages_ordered" AS
            SELECT
                Start,
                End,
                Velocity,
                Note,
                Message,
                Time,
                NoteID,
                TextureID
            FROM "midi_messages"
            ORDER BY Start;
        '''


    def insert_into_messages_table(self):
        return '''
            INSERT INTO "messages" (Start, End, Velocity, Note, Message, Time, NoteID, TextureID)
            SELECT Start, End, Velocity, Note, Message, Time, NoteID, TextureID
            FROM "midi_messages_ordered"
            ORDER BY Start ASC;
        '''