from pydantic import BaseModel, ConfigDict


class ChemicalCreate(BaseModel):
    product_name: str
    manufacturer: str | None = None
    description: str | None = None
    internal_code: str | None = None


class ChemicalRead(BaseModel):
    id: int
    product_name: str
    manufacturer: str | None = None
    description: str | None = None
    internal_code: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)