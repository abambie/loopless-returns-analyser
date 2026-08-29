from __future__ import annotations  # enables modern type-hint syntax (e.g. list[str]) on Python 3.9
from dataclasses import dataclass  # auto-generates __init__, __repr__, and __eq__ from the fields declared in each class
from datetime import date  # standard library date type — used for purchase_date fields
from typing import Optional, Dict, Any  # type hint aliases: Optional allows None, Dict/Any for flexible dicts


@dataclass(frozen=True)  # frozen=True makes all instances immutable (like a named tuple) — fields cannot be changed after creation
class Product:  # represents a single fashion product in the catalogue; holds all product metadata
    product_id: str  # unique identifier string for the product (e.g. "FB000123")
    category: str  # product category (e.g. "Dresses", "Shoes")
    brand: str  # the brand name (e.g. "Zara", "H&M")
    season: str  # the season this product is targeted at (e.g. "Summer", "Winter")
    size: str  # the size label (e.g. "S", "M", "XL")
    color: str  # the colour of the product (e.g. "Red", "Navy Blue")
    original_price: float  # the full retail price before any markdown
    markdown_percentage: float  # the percentage discount applied (e.g. 30.0 = 30% off)
    current_price: float  # the actual selling price after the markdown has been applied
    stock_quantity: int  # the number of units currently in stock
    customer_rating: float  # average customer rating out of 5.0

    def to_dict(self) -> Dict[str, Any]:  # converts the Product object into a plain Python dict for serialisation (e.g. JSON or DataFrame)
        return {  # return a dict with the same fields and values
            "product_id": self.product_id,  # copy product_id
            "category": self.category,  # copy category
            "brand": self.brand,  # copy brand
            "season": self.season,  # copy season
            "size": self.size,  # copy size
            "color": self.color,  # copy color
            "original_price": self.original_price,  # copy original_price
            "markdown_percentage": self.markdown_percentage,  # copy markdown_percentage
            "current_price": self.current_price,  # copy current_price
            "stock_quantity": self.stock_quantity,  # copy stock_quantity
            "customer_rating": self.customer_rating,  # copy customer_rating
        }


@dataclass(frozen=True)  # immutable dataclass — a ReturnReason value never changes once created
class ReturnReason:  # wraps a raw return reason string and adds normalisation helpers
    reason_text: str  # the raw return reason as stored in the database (e.g. "Sizing Issues", "Poor Quality")

    def normalise(self) -> str:  # returns a lowercased, whitespace-collapsed version for consistent comparisons
        return " ".join((self.reason_text or "").strip().lower().split())  # strip leading/trailing spaces, lowercase, then rejoin on single spaces

    def to_string(self) -> str:  # returns the original reason text unchanged
        return self.reason_text  # simple passthrough accessor


@dataclass(frozen=True)  # immutable dataclass — a purchase record's return status never changes after it is created
class PurchaseReturnRecord:  # represents one row from the purchases table, labelled as returned or not returned
    """
    Represents one purchase record labelled as returned/non-returned.

    Constraint (your UML note):
    - if is_returned == False -> return_reason must be None/empty
    - if is_returned == True  -> return_reason must be present
    """
    product_id: str  # the product this purchase relates to
    purchase_date: date  # the date the purchase was made
    is_returned: bool  # True if the customer returned this purchase, False if they kept it
    return_reason: Optional[str] = None  # the reason the customer gave for returning; None/empty if the item was not returned

    def to_dict(self) -> Dict[str, Any]:  # converts the record to a plain dict for serialisation
        return {  # return all fields as a dict
            "product_id": self.product_id,  # the product ID
            "purchase_date": self.purchase_date.isoformat(),  # convert the date to an ISO 8601 string (e.g. "2024-03-15") for JSON compatibility
            "is_returned": int(self.is_returned),  # convert bool to 0 or 1 for storage compatibility
            "return_reason": self.return_reason,  # the return reason string (or None)
        }


@dataclass(frozen=True)  # immutable dataclass — a scenario definition is set at construction time and never modified
class PolicyScenario:  # represents the configuration for a "what-if" simulation (e.g. "block all returns above 50% markdown")
    scenario_id: str  # unique identifier for this simulation run (e.g. "UI_SIM", "MODAL_SIM")
    name: str  # human-readable name for the scenario (e.g. "My Scenario")
    markdown_threshold: float  # any product with markdown_percentage >= this value is "restricted" by the policy (range 0–100)
    excluded_categories: list[str]  # list of category names to exclude from the simulation (treated as restricted)
    excluded_brands: list[str]  # list of brand names to exclude from the simulation
    excluded_seasons: list[str]  # list of season names to exclude from the simulation

    def validate(self) -> bool:  # checks that the scenario has a valid ID, name, and threshold before running the simulation
        if not self.scenario_id or not self.name:  # scenario_id and name must be non-empty strings
            return False  # invalid — reject
        if self.markdown_threshold < 0 or self.markdown_threshold > 100:  # threshold must be a valid percentage between 0 and 100
            return False  # invalid — reject
        return True  # all checks passed — scenario is valid

    def to_dict(self) -> Dict[str, Any]:  # converts the scenario to a plain dict for serialisation or logging
        return {  # return all fields as a dict
            "scenario_id": self.scenario_id,  # the scenario ID
            "name": self.name,  # the scenario name
            "markdown_threshold": self.markdown_threshold,  # the markdown threshold percentage
            "excluded_categories": self.excluded_categories,  # list of excluded categories
            "excluded_brands": self.excluded_brands,  # list of excluded brands
            "excluded_seasons": self.excluded_seasons,  # list of excluded seasons
        }


@dataclass(frozen=True)  # immutable dataclass — simulation results are computed once and never changed
class SimulationResult:  # holds the output of a policy simulation run
    scenario_id: str  # which scenario produced this result (matches PolicyScenario.scenario_id)
    baseline_return_rate: float  # the actual return rate in the data before the policy is applied (e.g. 0.32 = 32%)
    simulated_return_rate: float  # the modelled return rate if the policy had been applied (e.g. 0.28 = 28%)
    delta_return_rate: float  # the difference: simulated_return_rate - baseline_return_rate (negative = improvement)
    affected_return_count: int  # number of returns that would be prevented or affected by the policy

    def summarise(self) -> str:  # returns a human-readable one-line summary of the simulation result
        sign = "+" if self.delta_return_rate >= 0 else ""  # add a "+" prefix for positive (worsening) deltas; negative deltas already show "-"
        return (  # build and return a formatted summary string
            f"Scenario {self.scenario_id}: baseline={self.baseline_return_rate:.3f}, "  # show scenario ID and baseline rate to 3 dp
            f"simulated={self.simulated_return_rate:.3f}, delta={sign}{self.delta_return_rate:.3f}, "  # show simulated rate and signed delta
            f"affected_returns={self.affected_return_count}"  # show how many returns are affected
        )

    def to_dict(self) -> Dict[str, Any]:  # converts the result to a plain dict for serialisation (e.g. CSV export)
        return {  # return all fields as a dict
            "scenario_id": self.scenario_id,  # the scenario ID
            "baseline_return_rate": self.baseline_return_rate,  # the baseline rate as a decimal
            "simulated_return_rate": self.simulated_return_rate,  # the simulated rate as a decimal
            "delta_return_rate": self.delta_return_rate,  # the change in rate (negative = improvement)
            "affected_return_count": self.affected_return_count,  # the count of affected returns
        }


@dataclass(frozen=True)  # immutable dataclass — once a recommendation is created its text and priority never change
class Recommendation:  # a single generated recommendation shown on the Recommendations page
    title: str  # short headline for the recommendation (e.g. "High overall return rate detected")
    description: str  # full explanation of the recommendation and suggested action
    priority: str  # severity/priority level — one of "Low", "Medium", or "High"

    def to_dict(self) -> Dict[str, Any]:  # converts the recommendation to a plain dict for serialisation
        return {  # return all fields as a dict
            "title": self.title,  # the short title
            "description": self.description,  # the full description
            "priority": self.priority,  # the priority level string
        }
