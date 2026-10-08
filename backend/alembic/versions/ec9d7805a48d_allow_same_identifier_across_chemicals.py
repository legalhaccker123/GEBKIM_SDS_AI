"""allow same identifier across chemicals

Revision ID: ec9d7805a48d
Revises: cc2c54165c3d
Create Date: 2026-09-27

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "ec9d7805a48d"
down_revision: Union[str, Sequence[str], None] = "cc2c54165c3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    with op.batch_alter_table(
        "chemical_identifiers"
    ) as batch_op:

        # Eski global unique constraint kaldırılıyor:
        #
        # (identifier_type, identifier_value)
        #
        # Böylece aynı CAS farklı ticari ürünlerde
        # kullanılabilecek.

        batch_op.drop_constraint(
            "uq_identifier_type_value",
            type_="unique"
        )

        # Yeni constraint:
        #
        # Aynı Chemical içerisinde aynı identifier
        # iki kez oluşturulamaz.
        #
        # Ancak farklı Chemical kayıtları aynı
        # CAS / EC vb. identifier'ı kullanabilir.

        batch_op.create_unique_constraint(
            "uq_chemical_identifier_per_chemical",
            [
                "chemical_id",
                "identifier_type",
                "identifier_value",
            ]
        )


def downgrade() -> None:

    with op.batch_alter_table(
        "chemical_identifiers"
    ) as batch_op:

        batch_op.drop_constraint(
            "uq_chemical_identifier_per_chemical",
            type_="unique"
        )

        batch_op.create_unique_constraint(
            "uq_identifier_type_value",
            [
                "identifier_type",
                "identifier_value",
            ]
        )