"""Fresh users installation without images; existing installations are unsupported."""

from alembic import op
import sqlalchemy as sa

revision: str = "users_roles_20260927"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("surname", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("phone_number", sa.String(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("role", sa.String(), server_default="user", nullable=False),
        sa.Column(
            "is_blocked", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.CheckConstraint(
            "role IN ('user', 'admin', 'superadmin')", name="users_role_check"
        ),
        sa.CheckConstraint(
            "NOT is_blocked OR role = 'user'", name="users_blocked_role_check"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="users_email_key"),
        sa.UniqueConstraint("phone_number", name="users_phone_number_key"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index(
        "ux_users_superadmin",
        "users",
        ["role"],
        unique=True,
        postgresql_where=sa.text("role = 'superadmin'"),
        sqlite_where=sa.text("role = 'superadmin'"),
    )
    op.create_index("ix_users_created_at_id", "users", ["created_at", "id"])


def downgrade() -> None:
    op.drop_index("ix_users_created_at_id", table_name="users")
    op.drop_index("ux_users_superadmin", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
