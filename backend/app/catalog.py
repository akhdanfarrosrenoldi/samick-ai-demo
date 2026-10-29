"""Initial product entries for the independent catalog.

Prices are fictional values and must never be described as official.
"""

PRODUCTS = [
    {"id": "d-1", "name": "Greg Bennett D-1", "category": "Akustik Standard", "body": "Dreadnought", "top": "Mahogany", "back_sides": "Mahogany", "electronics": "Tidak ada", "color": "Natural", "price": 1750000, "image": "/products/d-1.jpg"},
    {"id": "d-1ce", "name": "Greg Bennett D-1CE", "category": "Akustik Standard", "body": "Dreadnought cutaway", "top": "Mahogany", "back_sides": "Mahogany", "electronics": "Clearwave10", "color": "Natural Mahogany", "price": 2450000, "image": "/products/d-1ce.jpg"},
    {"id": "gd-50-mini", "name": "Greg Bennett GD 50 MINI", "category": "Akustik Standard", "body": "Dreadnought mini", "top": "Spruce", "back_sides": "Sapele", "electronics": "Tidak ada", "color": "Open Pore / Natural", "price": 1950000, "image": "/products/gd-50-mini.jpg"},
    {"id": "om-1", "name": "Greg Bennett OM-1", "category": "Akustik Standard", "body": "Orchestra Model", "top": "Mahogany", "back_sides": "Mahogany", "electronics": "Tidak ada", "color": "Cokelat Sunburst", "price": 1890000, "image": "/products/om-1.jpg"},
    {"id": "gd100s", "name": "Greg Bennett GD100S", "category": "Akustik Intermediate", "body": "Dreadnought", "top": "Solid Spruce", "back_sides": "Mahogany", "electronics": "Tidak ada", "color": "Vintage Sunburst / Natural", "price": 3550000, "image": "/products/gd100s.jpg"},
    {"id": "gd100sce", "name": "Greg Bennett GD 100SCE", "category": "Akustik Intermediate", "body": "Dreadnought cutaway", "top": "Solid Spruce", "back_sides": "Mahogany", "electronics": "Fishman ISYS-T", "color": "Natural", "price": 4550000, "image": "/products/gd100sce.jpg"},
    {"id": "gom100rs", "name": "Greg Bennett GOM100RS", "category": "Akustik Intermediate", "body": "Orchestra Model", "top": "Solid Spruce", "back_sides": "Rosewood", "electronics": "Tidak ada", "color": "Natural", "price": 4250000, "image": "/products/gom100rs.jpg"},
    {"id": "d-5ce", "name": "Greg Bennett D-5CE", "category": "Akustik Pro", "body": "Dreadnought cutaway", "top": "Solid Engelmann Spruce", "back_sides": "Sapele", "electronics": "Clearwave60 / Fishman", "color": "Natural", "price": 6650000, "image": "/products/d-5ce.jpg"},
    {"id": "om-5", "name": "Greg Bennett OM-5", "category": "Akustik Pro", "body": "Orchestra Model", "top": "Solid Engelmann Spruce", "back_sides": "Sapele", "electronics": "Tidak ada", "color": "Natural", "price": 5950000, "image": "/products/om-5.jpg"},
    {"id": "ss70-white", "name": "Samick SS70 White", "category": "Elektrik", "body": "Solid body", "top": "Nyatoh", "back_sides": "Nyatoh", "electronics": "Humbucker 403 Up & Down", "color": "Putih", "price": 3150000, "image": "/products/ss70-white.jpg"},
]

def public_product(product: dict) -> dict:
    fields = ("id", "name", "category", "body", "top", "back_sides", "electronics", "color", "image")
    return {field: product[field] for field in fields}
