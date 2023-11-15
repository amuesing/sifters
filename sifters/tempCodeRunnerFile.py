    def generate_create_and_insert_end_data_commands(self, texture_id):
        create_table_command = f'''
        CREATE TABLE "texture_{texture_id}_end_column" (
            Note_ID INTEGER,  -- Add Note_ID column
            Texture_ID INTEGER,  -- Add Texture_ID column
            Start INTEGER, 
            End INTEGER, 
            Duration INTEGER,
            Velocity INTEGER, 
            Note TEXT
        );
        '''

        insert_data_command = f'''
        WITH ModifiedDurations AS (
            SELECT 
                Note_ID,  -- Include Note_ID
                Texture_ID,  -- Include Texture_ID
                Start,
                Velocity,
                Note,
                Duration as ModifiedDuration
            FROM "texture_{texture_id}_max_duration"
        ),
        DistinctEnds AS (
            SELECT
                Note_ID,  -- Include Note_ID
                Texture_ID,  -- Include Texture_ID
                Start,
                COALESCE(LEAD(Start, 1) OVER(ORDER BY Start), Start + ModifiedDuration) AS End
            FROM (SELECT DISTINCT Note_ID, Texture_ID, Start, ModifiedDuration FROM ModifiedDurations) as distinct_starts
        )
        INSERT INTO "texture_{texture_id}_end_column"
        SELECT 
            m.Note_ID,  -- Include Note_ID
            m.Texture_ID,  -- Include Texture_ID
            m.Start,
            d.End,
            m.ModifiedDuration,
            m.Velocity,
            m.Note
        FROM ModifiedDurations m
        JOIN DistinctEnds d ON m.Start = d.Start;
        '''

        return create_table_command + '\n' + insert_data_command