from pydantic import BaseModel, Field, model_validator


class StaffPermissions(BaseModel):
    manage_inventory: bool = False
    receive_stock: bool = False
    view_purchase_costs: bool = False
    apply_discounts: bool = False
    process_returns: bool = False


class LoginInput(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class PlatformLoginInput(LoginInput):
    pass


class PlatformStoreInput(BaseModel):
    store_name: str = Field(min_length=2, max_length=100)
    business_type: str = Field(default="general", pattern="^(general|supermarket|fashion|footwear|other)$")
    currency: str = Field(default="INR", pattern="^(INR|USD|EUR|GBP|AUD|CAD)$")
    owner_name: str = Field(min_length=2, max_length=100)
    owner_email: str = Field(min_length=5, max_length=254)
    owner_password: str = Field(min_length=8, max_length=128)


class ProductInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    brand: str = Field(default="", max_length=100)
    category: str = Field(default="General", max_length=80)
    sku: str = Field(default="", max_length=80)
    size: str = Field(default="", max_length=40)
    color: str = Field(default="", max_length=40)
    unit: str = Field(default="each", max_length=24)
    tax_rate: float = Field(default=0, ge=0, le=100)
    expiry_date: str = Field(default="", max_length=20)
    price: float = Field(gt=0)
    cost: float = Field(default=0, ge=0)
    stock: float = Field(default=0, ge=0)
    reorder_level: float = Field(default=5, ge=0)


class LineInput(BaseModel):
    product_id: int
    quantity: float = Field(gt=0, le=10000)


class SaleInput(BaseModel):
    items: list[LineInput] = Field(min_length=1)
    discount: float = Field(default=0, ge=0)
    payment_method: str = Field(default="card", pattern="^(card|cash|upi|other)$")


class StaffInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    permissions: StaffPermissions = Field(default_factory=StaffPermissions)


class StaffPermissionsInput(BaseModel):
    permissions: StaffPermissions


class SupplierInput(BaseModel):
    name: str = Field(min_length=2, max_length=140)
    contact_name: str = Field(default="", max_length=100)
    email: str = Field(default="", max_length=254)
    phone: str = Field(default="", max_length=40)
    address: str = Field(default="", max_length=300)


class PurchaseLineInput(BaseModel):
    product_id: int
    quantity: float = Field(gt=0, le=100000)
    unit_cost: float = Field(ge=0)
    tax_rate: float = Field(default=0, ge=0, le=100)
    batch_number: str = Field(default="", max_length=100)
    expiry_date: str = Field(default="", max_length=20)


class PurchaseInput(BaseModel):
    supplier_id: int
    invoice_number: str = Field(min_length=1, max_length=100)
    invoice_date: str = Field(min_length=8, max_length=20)
    freight: float = Field(default=0, ge=0)
    paid_amount: float = Field(default=0, ge=0)
    items: list[PurchaseLineInput] = Field(min_length=1)


class ExpenseInput(BaseModel):
    category: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0)
    expense_date: str = Field(min_length=8, max_length=20)


class ImportProductsInput(BaseModel):
    products: list[ProductInput] = Field(min_length=1, max_length=5000)


class ReturnLineInput(BaseModel):
    sale_item_id: int
    quantity: float = Field(gt=0, le=10000)
    restock: bool = True


class ReturnInput(BaseModel):
    items: list[ReturnLineInput] = Field(min_length=1)

    @model_validator(mode="after")
    def ensure_unique_sale_lines(self):
        item_ids = [item.sale_item_id for item in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("A sale line can appear only once in a return.")
        return self


class StockAdjustmentInput(BaseModel):
    product_id: int
    quantity: float = Field(ne=0)
    reason: str = Field(min_length=2, max_length=200)


class RegisterOpenInput(BaseModel):
    opening_cash: float = Field(ge=0)


class RegisterCloseInput(BaseModel):
    counted_cash: float = Field(ge=0)


class RazorpayOrderInput(BaseModel):
    items: list[LineInput] = Field(min_length=1)
    discount: float = Field(default=0, ge=0)


class RazorpayVerifyInput(BaseModel):
    razorpay_order_id: str = Field(min_length=5, max_length=80)
    razorpay_payment_id: str = Field(min_length=5, max_length=80)
    razorpay_signature: str = Field(min_length=64, max_length=128, pattern="^[a-fA-F0-9]+$")
