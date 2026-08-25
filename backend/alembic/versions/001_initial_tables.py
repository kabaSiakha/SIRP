"""Creation des tables initiales: users, incidents, comments, audit_logs

Revision ID: 001
Revises: None
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Table users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("username", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("role", sa.Enum("admin", "analyst", "reporter", name="userrole"), nullable=False, server_default="reporter"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Table incidents
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.Enum("low", "medium", "high", "critical", name="incidentseverity"), nullable=False),
        sa.Column("status", sa.Enum("open", "in_progress", "resolved", "closed", name="incidentstatus"), nullable=False, server_default="open"),
        sa.Column("category", sa.Enum("malware", "phishing", "data_breach", "ddos", "unauthorized_access", "insider_threat", "ransomware", "other", name="incidentcategory"), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_to", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
    )

    # Table comments
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Table audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("comments")
    op.drop_table("incidents")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS incidentseverity")
    op.execute("DROP TYPE IF EXISTS incidentstatus")
    op.execute("DROP TYPE IF EXISTS incidentcategory")
