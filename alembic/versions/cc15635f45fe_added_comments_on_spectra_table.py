"""added comments on spectra table

Revision ID: cc15635f45fe
Revises: c867ada3e0c4
Create Date: 2021-04-20 22:15:45.241664

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc15635f45fe'
down_revision = 'c867ada3e0c4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'commentsonspectra',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column(
            'ctype', sa.Enum('text', 'redshift', name='comment_types'), nullable=True
        ),
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
        op.f('ix_commentsonspectra_author_id'),
        'commentsonspectra',
        ['author_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_commentsonspectra_created_at'),
        'commentsonspectra',
        ['created_at'],
        unique=False,
    )
    op.create_index(
        op.f('ix_commentsonspectra_obj_id'),
        'commentsonspectra',
        ['obj_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_commentsonspectra_spectrum_id'),
        'commentsonspectra',
        ['spectrum_id'],
        unique=False,
    )
    op.create_table(
        'group_comments_on_spectra',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified', sa.DateTime(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('commentonspectrum_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['commentonspectrum_id'], ['commentsonspectra.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'group_comments_on_spectra_forward_ind',
        'group_comments_on_spectra',
        ['group_id', 'commentonspectrum_id'],
        unique=True,
    )
    op.create_index(
        'group_comments_on_spectra_reverse_ind',
        'group_comments_on_spectra',
        ['commentonspectrum_id', 'group_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_group_comments_on_spectra_created_at'),
        'group_comments_on_spectra',
        ['created_at'],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
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
        op.f('ix_commentsonspectra_spectrum_id'), table_name='commentsonspectra'
    )
    op.drop_index(op.f('ix_commentsonspectra_obj_id'), table_name='commentsonspectra')
    op.drop_index(
        op.f('ix_commentsonspectra_created_at'), table_name='commentsonspectra'
    )
    op.drop_index(
        op.f('ix_commentsonspectra_author_id'), table_name='commentsonspectra'
    )
    op.drop_table('commentsonspectra')
    # ### end Alembic commands ###
