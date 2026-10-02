"""Normalize two user roles and preserve the protected administrator."""

from alembic import op
import sqlalchemy as sa

revision: str = "role_catalog_20260927"
down_revision: str | None = "users_roles_20260927"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    roles = op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("value", name="roles_value_key"),
        sa.CheckConstraint(
            "(id = 1 AND value = 'user') OR (id = 2 AND value = 'admin')",
            name="roles_catalog_check",
        ),
    )
    op.bulk_insert(
        roles,
        [
            {"id": 1, "value": "user", "label": "Пользователь"},
            {"id": 2, "value": "admin", "label": "Администратор"},
        ],
    )
    op.add_column("users", sa.Column("role_id", sa.Integer(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "is_superadmin", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
    )
    op.execute(
        "UPDATE users SET role_id = CASE WHEN role = 'user' THEN 1 ELSE 2 END, "
        "is_superadmin = CASE WHEN role = 'superadmin' THEN true ELSE false END"
    )
    op.drop_index("ux_users_superadmin", table_name="users")
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("users_role_check", type_="check")
        batch.drop_constraint("users_blocked_role_check", type_="check")
        batch.alter_column(
            "role_id",
            existing_type=sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        )
        batch.create_foreign_key(
            "users_role_id_fkey", "roles", ["role_id"], ["id"], ondelete="RESTRICT"
        )
        batch.create_check_constraint("users_role_id_check", "role_id IN (1, 2)")
        batch.create_check_constraint(
            "users_blocked_role_check", "NOT is_blocked OR role_id = 1"
        )
        batch.create_check_constraint(
            "users_superadmin_role_check", "NOT is_superadmin OR role_id = 2"
        )
        batch.drop_column("role")
    op.create_index(
        "ux_users_superadmin",
        "users",
        ["is_superadmin"],
        unique=True,
        postgresql_where=sa.text("is_superadmin"),
        sqlite_where=sa.text("is_superadmin"),
    )


def downgrade() -> None:
    op.add_column(
        "users", sa.Column("role", sa.String(), server_default="user", nullable=False)
    )
    op.execute(
        "UPDATE users SET role = CASE WHEN is_superadmin THEN 'superadmin' "
        "WHEN role_id = 2 THEN 'admin' ELSE 'user' END"
    )
    op.drop_index("ux_users_superadmin", table_name="users")
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("users_role_id_fkey", type_="foreignkey")
        batch.drop_constraint("users_role_id_check", type_="check")
        batch.drop_constraint("users_blocked_role_check", type_="check")
        batch.drop_constraint("users_superadmin_role_check", type_="check")
        batch.drop_column("role_id")
        batch.drop_column("is_superadmin")
        batch.create_check_constraint(
            "users_role_check", "role IN ('user', 'admin', 'superadmin')"
        )
        batch.create_check_constraint(
            "users_blocked_role_check", "NOT is_blocked OR role = 'user'"
        )
    op.create_index(
        "ux_users_superadmin",
        "users",
        ["role"],
        unique=True,
        postgresql_where=sa.text("role = 'superadmin'"),
        sqlite_where=sa.text("role = 'superadmin'"),
    )
    op.drop_table("roles")
