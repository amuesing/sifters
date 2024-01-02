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
        self.create_notes_table()
        self.create_messages_table()
        self.insert_dataframe_into_database(mediator.notes_data)
        self.set_database_tables()

    
    def create_table(self, table_name, columns):
        sql_command = f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                {columns}
            )'''
        self.cursor.execute(sql_command)
        self.connection.commit()


    def create_notes_table(self):
        columns = '''
            Start INTEGER,
            Velocity INTEGER,
            Note TEXT,
            Duration INTEGER,
            note_id INTEGER PRIMARY KEY
        '''
        self.create_table("notes", columns)


    def create_messages_table(self):
        columns = '''
            Start INTEGER,
            End INTEGER,
            Velocity INTEGER,
            Note INTEGER,
            Message TEXT,
            Time INTEGER,
            message_id INTEGER PRIMARY KEY,
            note_id INTEGER
        '''
        self.create_table("messages", columns)

        
    def insert_dataframe_into_database(self, dataframe):
        # Insert notes data into notes table
        dataframe.to_sql(name='notes', con=self.connection, if_exists='append', index=False)


    def fetch_columns_by_table_name(self, table_name, exclude_columns={}):
        # Get the first row for the given table_name
        self.cursor.execute(f'SELECT * FROM "{table_name}"')
        row = self.cursor.fetchone()
        # Use the keys of the row (which are column names) and filter out the ones in the exclude set
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
    

    def generate_sql_for_duration_values(self, columns_list):
        columns_string = ', '.join(columns_list)
        duration_values = [grid * self.scaling_factor for grid in self.grids_set]
        length_of_reps = [int(math.pow(self.period, 2) * duration) for duration in duration_values]

        table_commands = {}
        for duration_value, length_of_one_rep, repeat in zip(duration_values, length_of_reps, self.repeats):
            table_name = f"matrix_{duration_value}"
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
        return '''
        CREATE TEMPORARY TABLE "max_duration" AS
        WITH max_durations AS (
            SELECT Start, MAX(Duration) as MaxDuration
            FROM "notes"
            GROUP BY Start
        )
        SELECT c.note_id, c.Start, c.Velocity, c.Note, m.MaxDuration as Duration
        FROM "notes" c
        LEFT JOIN max_durations m ON c.Start = m.Start;
        '''

    
    def generate_create_and_insert_end_data_commands(self):
        create_table_command = '''
        CREATE TEMPORARY TABLE "end_column" (
            note_id INTEGER,
            Start INTEGER, 
            End INTEGER, 
            Duration INTEGER,
            Velocity INTEGER, 
            Note TEXT
        );
        '''

        insert_data_command = '''
        WITH ModifiedDurations AS (
            SELECT 
                note_id,
                Start,
                Velocity,
                Note,
                Duration as ModifiedDuration
            FROM "max_duration"
        ),
        DistinctEnds AS (
            SELECT
                Start,
                COALESCE(LEAD(Start, 1) OVER(ORDER BY Start), Start + ModifiedDuration) AS End
            FROM (SELECT DISTINCT Start, ModifiedDuration FROM ModifiedDurations) as distinct_starts
        )
        INSERT INTO "end_column"
        SELECT
            m.note_id,
            m.Start,
            d.End,
            m.ModifiedDuration,
            m.Velocity,
            m.Note
        FROM ModifiedDurations m
        JOIN DistinctEnds d ON m.Start = d.Start;
        '''

        return create_table_command + '\n' + insert_data_command

        
    def generate_find_duplicate_rows_command(self):
        return '''
        CREATE TEMPORARY TABLE "duplicates" AS
        SELECT
            *
        FROM end_column
        WHERE (Start, End, Velocity, Note) IN (
            SELECT
                Start,
                End,
                Velocity,
                Note
            FROM end_column
            GROUP BY Start, End, Velocity, Note
            HAVING COUNT(*) > 1
        );
        '''

        
    def generate_filter_duplicate_rows_command(self):
        return '''
        CREATE TEMPORARY TABLE "no_duplicates" AS
        SELECT
            note_id,
            Start,
            End,
            Velocity,
            Note
        FROM (
            SELECT
                note_id,
                Start,
                End,
                Velocity,
                Note,
                ROW_NUMBER() OVER (PARTITION BY Start, End, Velocity, Note ORDER BY (SELECT NULL)) AS row_num
            FROM end_column
        )
        WHERE row_num = 1;
        '''

        
        
    def generate_notes_table_commands(self):
        commands = []
        commands.append(self.generate_max_duration_command())
        commands.append(self.generate_create_and_insert_end_data_commands())
        commands.append(self.generate_find_duplicate_rows_command())
        commands.append(self.generate_filter_duplicate_rows_command())

        return '\n'.join(commands)

    
    def create_temporary_midi_messages_table(self):
        return f'''
            CREATE TEMPORARY TABLE "midi_messages" AS
            SELECT 
                note_id,
                Start,
                End,
                Velocity,
                Note,
                'note_on' AS Message,
                CASE 
                    WHEN ROW_NUMBER() OVER (ORDER BY Start ASC) = 1 AND Start != 0 THEN ROUND(Start * {self.ticks_per_beat})
                    ELSE 0 
                END AS Time
            FROM "no_duplicates";
        '''


    def update_time_column(self):
        return '''
            UPDATE "midi_messages"
            SET Time = (
                SELECT COALESCE("midi_messages".Start - t.PreviousEnd, 0)
                FROM (
                    SELECT 
                        Start,
                        LAG(End) OVER (ORDER BY Start ASC) AS PreviousEnd
                    FROM "midi_messages"
                ) AS t
                WHERE 
                    "midi_messages".Start = t.Start
            )
            WHERE EXISTS (
                SELECT 1
                FROM (
                    SELECT 
                        Start,
                        LAG(End) OVER (ORDER BY Start ASC) AS PreviousEnd,
                        LAG(Start) OVER (ORDER BY Start ASC) AS PreviousStart
                    FROM "midi_messages"
                ) AS t_sub
                WHERE 
                    "midi_messages".Start = t_sub.Start 
                    AND "midi_messages".Start != t_sub.PreviousEnd
                    AND "midi_messages".Start != t_sub.PreviousStart
            );
        '''

        
    def append_note_off_message(self):
        return f'''
            INSERT INTO "midi_messages" (note_id, Start, End, Velocity, Note, Message, Time)
            SELECT 
                note_id, Start, End, Velocity, Note,
                'note_off' AS Message,
                (End - Start) * {self.ticks_per_beat} AS Time
            FROM "midi_messages" AS t
            WHERE Message = 'note_on';
        '''


    def order_matrix_table_by_start(self):
        return '''
            CREATE TEMPORARY TABLE "midi_messages_ordered" AS
            SELECT
                note_id,
                Start,
                End,
                Velocity,
                Note,
                Message,
                CASE
                    WHEN Message = 'note_off' AND LAG(Message) OVER (ORDER BY Start) = 'note_off'
                        THEN 0
                    ELSE Time
                END AS Time
            FROM "midi_messages"
            ORDER BY Start;
        '''


    def insert_into_messages_table(self):
        return '''
            INSERT INTO "messages" (note_id, Start, End, Velocity, Note, Message, Time)
            SELECT note_id, Start, End, Velocity, Note, Message, Time
            FROM "midi_messages_ordered"
            ORDER BY Start ASC;
        '''



    def generate_midi_messages_table_commands(self):
        command = []
        command.append(self.create_temporary_midi_messages_table())
        command.append(self.update_time_column())
        command.append(self.append_note_off_message())
        command.append(self.order_matrix_table_by_start())
        command.append(self.insert_into_messages_table())

        return '\n'.join(command)

    
    def set_database_tables(self):
        table_names = []

        columns_list = self.fetch_columns_by_table_name('notes', exclude_columns={'note_id', 'Start', 'Duration'})

        table_commands = self.generate_sql_for_duration_values(columns_list)

        for table_name, union_statements in table_commands.items():
            table_names.append(table_name)
            self.cursor.execute(f'CREATE TEMPORARY TABLE "{table_name}" AS {union_statements};')

        self.cursor.execute('DELETE FROM notes;')
        self.cursor.executescript(self.insert_into_notes_command(table_names))

        sql_commands = [
                self.generate_notes_table_commands(),
                self.generate_midi_messages_table_commands(),
                ]
        
        combined_sql = "\n".join(sql_commands)
        self.cursor.executescript(combined_sql)
        self.connection.commit()