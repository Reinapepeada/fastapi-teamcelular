from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import product_r, branches_r, categories_r, brands_r

app = FastAPI(
    title="Team Celular API",
    description="API para catálogo de productos de Team Celular",
    version="1.0.0"
)

# Configurar los orígenes permitidos
origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://teamcelular.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas principales para el catálogo de productos
app.include_router(product_r.router, tags=["Products"], prefix="/products")
app.include_router(branches_r.router, tags=["Branches"], prefix="/branches")
app.include_router(categories_r.router, tags=["Categories"], prefix="/categories")
app.include_router(brands_r.router, tags=["Brands"], prefix="/brands")


@app.get("/")
def read_root():
    return {"msg": "Welcome to Team Celular's API!"}




