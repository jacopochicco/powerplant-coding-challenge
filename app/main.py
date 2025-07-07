from fastapi import FastAPI
from pydantic import BaseModel, Field, ConfigDict
from typing import List

class Fuels(BaseModel):
    gas: float = Field(..., alias="gas(euro/MWh)")
    kerosine: float = Field(..., alias="kerosine(euro/MWh)")
    co2: float = Field(..., alias="co2(euro/ton)")
    wind: float = Field(..., alias="wind(%)")
    model_config = ConfigDict(validate_by_name=True)

class PowerPlant(BaseModel):
    name: str
    type: str
    efficiency: float
    pmin: float
    pmax: float

class ProductionPlanRequest(BaseModel):
    load: float
    fuels: Fuels
    powerplants: List[PowerPlant]

app = FastAPI()

@app.post("/productionplan")
def generate_production_plan(payload: ProductionPlanRequest):
    load_remaining = payload.load
    fuels = payload.fuels
    powerplants = payload.powerplants

    # Calculate cost per MWh
    def calculate_cost(plant: PowerPlant) -> float:
        if plant.type == "windturbine":
            return 0
        elif plant.type == "gasfired":
            return fuels.gas / plant.efficiency
        elif plant.type == "turbojet":
            return fuels.kerosine / plant.efficiency
        return float("inf")

    # Adjust max power for wind turbines
    for plant in powerplants:
        if plant.type == "windturbine":
            plant.pmax = plant.pmax * fuels.wind / 100
    # Sort by cost
    sorted_plants = sorted(powerplants, key=calculate_cost)

    # Allocate production
    production = []
    for plant in sorted_plants:
        power = 0
        if load_remaining >  0:
            if load_remaining >= plant.pmin:
                power = min(load_remaining, plant.pmax)
            else:
                # We try to reduce the use of the last processed plant (but not less than its minimum)
                # to be able to use the current plant, meaning having a production greater than its minimum
                if len(production) > 0:
                    possible_production_reduction = min(plant.pmin-load_remaining, production[-1]["p"] - production[-1]["pmin"])
                    power = min(load_remaining+possible_production_reduction, plant.pmax)
                    if power >= plant.pmin:
                        production[-1]["p"] -= possible_production_reduction 
                        load_remaining += possible_production_reduction
                    else:
                        power = 0
            load_remaining -= power

        production.append({"name": plant.name, "p": round(power, 1), "pmin": plant.pmin})

    return list(map(lambda plant: {"name": plant["name"], "p": plant["p"]} , production))
