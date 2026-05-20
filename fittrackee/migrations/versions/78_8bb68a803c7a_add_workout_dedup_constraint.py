"""add unique constraint on (user_id, workout_date) for deduplication

Revision ID: 8bb68a803c7a
Revises: 3d0c336b7a9e
Create Date: 2026-05-20 16:25:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '8bb68a803c7a'
down_revision = '3d0c336b7a9e'
branch_labels = None
depends_on = None


def upgrade():
    # Identify duplicate workout IDs (all except the lowest id per user+date).
    # Must delete child rows first due to FK constraints.
    op.execute("""
        DELETE FROM workout_segments
        WHERE workout_id IN (
            SELECT id FROM workouts
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM workouts
                GROUP BY user_id, workout_date
            )
        )
    """)
    op.execute("""
        DELETE FROM records
        WHERE workout_id IN (
            SELECT id FROM workouts
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM workouts
                GROUP BY user_id, workout_date
            )
        )
    """)
    op.execute("""
        DELETE FROM workouts
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM workouts
            GROUP BY user_id, workout_date
        )
    """)

    with op.batch_alter_table('workouts', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'user_id_workout_date_unique', ['user_id', 'workout_date']
        )


def downgrade():
    with op.batch_alter_table('workouts', schema=None) as batch_op:
        batch_op.drop_constraint(
            'user_id_workout_date_unique', type_='unique'
        )
