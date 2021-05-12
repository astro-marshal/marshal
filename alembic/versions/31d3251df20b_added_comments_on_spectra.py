"""added comments on spectra

Revision ID: 31d3251df20b
Revises: 0595e877f471
Create Date: 2021-05-11 21:31:31.638187

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '31d3251df20b'
down_revision = '0595e877f471'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'comments_on_spectra',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('attachment_name', sa.String(), nullable=True),
        sa.Column('attachment_bytes', sa.LargeBinary(), nullable=True),
        sa.Column('origin', sa.String(), nullable=True),
        sa.Column('spectrum_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('obj_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['obj_id'], ['objs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['spectrum_id'], ['spectra.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_comments_on_spectra_author_id'),
        'comments_on_spectra',
        ['author_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_comments_on_spectra_created_at'),
        'comments_on_spectra',
        ['created_at'],
        unique=False,
    )
    op.create_index(
        op.f('ix_comments_on_spectra_obj_id'),
        'comments_on_spectra',
        ['obj_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_comments_on_spectra_spectrum_id'),
        'comments_on_spectra',
        ['spectrum_id'],
        unique=False,
    )
    op.create_table(
        'group_comments_on_spectra',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('comments_on_spectr_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['comments_on_spectr_id'], ['comments_on_spectra.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'group_comments_on_spectra_forward_ind',
        'group_comments_on_spectra',
        ['group_id', 'comments_on_spectr_id'],
        unique=True,
    )
    op.create_index(
        'group_comments_on_spectra_reverse_ind',
        'group_comments_on_spectra',
        ['comments_on_spectr_id', 'group_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_group_comments_on_spectra_created_at'),
        'group_comments_on_spectra',
        ['created_at'],
        unique=False,
    )
    op.drop_column('comments', 'ctype')
    # ### end Alembic commands ###

    op.execute('DROP TYPE "public"."comment_types"')
    op.execute(
        'ALTER TYPE "public"."followup_apis" RENAME TO "followup_apis__old_version_to_be_dropped"'
    )
    op.execute(
        '''CREATE TYPE "public"."followup_apis" AS ENUM ('SEDMAPI', 'IOOAPI', 'IOIAPI', 'SPRATAPI', 'SINISTROAPI', 'SPECTRALAPI', 'FLOYDSAPI', 'MUSCATAPI')'''
    )
    op.execute(
        'ALTER TABLE "public"."instruments" ALTER COLUMN api_classname TYPE "public"."followup_apis" USING api_classname::text::"public"."followup_apis"'
    )
    op.execute('DROP TYPE "public"."followup_apis__old_version_to_be_dropped"')


def downgrade():
    op.execute('CREATE TYPE comment_types AS ENUM ("text", "redshift"")')
    op.execute('CREATE TYPE followup_apis__old_version_to_be_dropped')
    op.execute(
        'ALTER TABLE "public"."instruments" ALTER COLUMN api_classname TYPE api_classname::text::"public"."followup_apis" USING "public"."followup_apis"'
    )
    op.execute('DROP TYPE  "public"."followup_apis"')
    op.execute(
        'ALTER TYPE "followup_apis__old_version_to_be_dropped" RENAME TO "public"."followup_apis"'
    )

    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'comments',
        sa.Column(
            'ctype',
            postgresql.ENUM('text', 'redshift', name='comment_types'),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.drop_index(
        op.f('ix_group_comments_on_spectra_created_at'),
        table_name='group_comments_on_spectra',
    )
    op.drop_index(
        'group_comments_on_spectra_reverse_ind', table_name='group_comments_on_spectra'
    )
    op.drop_index(
        'group_comments_on_spectra_forward_ind', table_name='group_comments_on_spectra'
    )
    op.drop_table('group_comments_on_spectra')
    op.drop_index(
        op.f('ix_comments_on_spectra_spectrum_id'), table_name='comments_on_spectra'
    )
    op.drop_index(
        op.f('ix_comments_on_spectra_obj_id'), table_name='comments_on_spectra'
    )
    op.drop_index(
        op.f('ix_comments_on_spectra_created_at'), table_name='comments_on_spectra'
    )
    op.drop_index(
        op.f('ix_comments_on_spectra_author_id'), table_name='comments_on_spectra'
    )
    op.drop_table('comments_on_spectra')
    # ### end Alembic commands ###
