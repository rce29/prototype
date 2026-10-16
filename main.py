
import streamlit as st
import pandas as pd
import uuid
from supabase import create_client

@st.cache_resource
def connect_to_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_SECRET_KEY"]
    )

try:
    supabase = connect_to_supabase()
except Exception:
    st.error(
        "Database connection failed."
    )
    st.stop()

defaults = {
    "sustainability_interest": None,
    "questionnaire_completed": False,
    "show_questionnaire": False,
    "step": 0,
    "selected_products": {},
    "participant_id": str(uuid.uuid4()),
    "response_saved": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

if not st.session_state.questionnaire_completed:

    st.title("Winter Fashion Shop")

    st.write("Before you start, please answer one short question.")

    st.subheader("How interested are you in sustainable shopping?")

    interest_options = [
        "Not interested at all",
        "Slightly interested",
        "Moderately interested",
        "Very interested",
        "Extremely interested"
    ]

    selected_interest = st.radio(
        "Please select one answer:",
        interest_options,
        index=None
    )

    if st.button("Continue to Shop", type="primary"):

        if selected_interest is not None:
            st.session_state.sustainability_interest = selected_interest
            st.session_state.questionnaire_completed = True
            st.rerun()
        else:
            st.warning("Please select an answer first.")

    st.stop()

if not st.session_state.show_questionnaire:

    df = pd.read_csv("Winter_Fashion_Dataset.csv")

    st.title("Winter Fashion Shop")
    st.write("Choose your products and create your winter outfit!")

    st.info(
        "**Sustainability Score:** The score ranges from 1 to 5. "
        "1 = less sustainable, 5 = more sustainable."
    )

    products = ["Sweater", "Coat", "Beanie", "Boots"]

    product = products[st.session_state.step]

    nudging_techniques = {
        "Sweater": "Control",
        "Coat": "Labels",
        "Beanie": "Prioritization",
        "Boots": "Framing"
    }

    nudging_technique = nudging_techniques[product]

    st.header(f"Choose your {product}")

    result = df[df["Category"] == product].copy()

    if nudging_technique == "Prioritization":
        result = result.sort_values(
            by="Sustainability",
            ascending=False
        )

    previous_selection = st.session_state.selected_products.get(product)

    columns = st.columns(3)

    for i, (_, row) in enumerate(result.iterrows()):

        product_id = str(row["Product_ID"])

        with columns[i % 3]:

            if nudging_technique == "Labels" and row["Sustainability"] == 5:
                st.subheader(str(row["Colour"]) + " 🌱")
            else:
                st.subheader(str(row["Colour"]))

            st.write(f"**Price:** {row['Price_EUR']} €")
            st.write(f"**Material:** {row['Material']}")
            st.write(
                f"**Sustainability Score (1-5):** {row['Sustainability']}"
            )

            if (
                nudging_technique == "Framing"
                and row["Sustainability"] == 5
            ):
                st.info(
                    "**Positive impact:** This product has a relatively "
                    "high sustainability score."
                )

            if previous_selection == product_id:
                st.success("Selected")

            if st.button(
                "Select",
                key=f"select_{product}_{product_id}",
                use_container_width=True
            ):
                st.session_state.selected_products[product] = product_id
                st.rerun()

    st.write("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.session_state.step > 0:
            if st.button("Back", use_container_width=True):
                st.session_state.step -= 1
                st.rerun()

    with col2:
        if st.session_state.step < len(products) - 1:
            if st.button("Next", use_container_width=True):

                if product in st.session_state.selected_products:
                    st.session_state.step += 1
                    st.rerun()
                else:
                    st.warning("Please select a product first.")

        else:
            if st.button("Submit", use_container_width=True):

                if product in st.session_state.selected_products:
                    st.session_state.show_questionnaire = True
                    st.rerun()
                else:
                    st.warning("Please select a product first.")

else:

    st.title("Final Questionnaire")

    st.write(
        "Please rank the following factors according to how strongly "
        "they influenced your product choices."
    )

    st.write(
        "1 = Influenced me the least | 4 = Influenced me the most. "
        "Use each number only once."
    )

    factors = [
        "Material",
        "Colour",
        "Sustainability Score",
        "Price"
    ]

    rankings = {}

    for factor in factors:
        rankings[factor] = st.selectbox(
            factor,
            options=[1, 2, 3, 4],
            index=None,
            key=f"ranking_{factor}"
        )

    if st.session_state.response_saved:
        st.success("Thank you for your participation!")

    elif st.button("Submit Questionnaire", type="primary"):

        if any(value is None for value in rankings.values()):
            st.warning("Please rank all four factors.")

        elif len(set(rankings.values())) != 4:
            st.warning("Please use each rank only once.")

        elif any(
            category not in st.session_state.selected_products
            for category in ["Sweater", "Coat", "Beanie", "Boots"]
        ):
            st.warning("Please select one product from every category.")

        else:

            response = {
                "participant_id": st.session_state.participant_id,

                "sweater_id": st.session_state.selected_products["Sweater"],
                "coat_id": st.session_state.selected_products["Coat"],
                "beanie_id": st.session_state.selected_products["Beanie"],
                "boot_id": st.session_state.selected_products["Boots"],

                "material_rank": rankings["Material"],
                "colour_rank": rankings["Colour"],
                "sustainability_rank": rankings["Sustainability Score"],
                "price_rank": rankings["Price"],

                "sustainability_interest":
                    st.session_state.sustainability_interest
            }

            supabase.table("study_responses").insert(
                response
            ).execute()

            st.session_state.response_saved = True
            st.success("Thank you for your participation!")

