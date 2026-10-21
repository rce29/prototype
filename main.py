
import os
import uuid

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not url or not supabase_key:
    st.error("SUPABASE_URL or SUPABASE_KEY is missing from the .env file.")
    st.stop()

supabase: Client = create_client(url, supabase_key)


defaults = {
    "page": "welcome",
    "consent_given": False,
    "sustainability_interest": None,
    "age": None,
    "gender": None,
    "assigned_condition": None,
    "step": 0,
    "selected_products": {},
    "participant_id": str(uuid.uuid4()),
    "response_saved": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def go_to(page):
    st.session_state.page = page
    st.rerun()


def assign_condition():
    if st.session_state.assigned_condition is None:
        response = supabase.rpc(
            "assign_study_condition",
            {
                "p_participant_id": st.session_state.participant_id
            },
        ).execute()

        st.session_state.assigned_condition = response.data

    return st.session_state.assigned_condition


if st.session_state.page == "welcome":
    st.title("Welcome to the Online Fashion Shop Study")

    st.write(
        "Thank you for considering taking part in this study. "
        "You will browse a simulated online fashion shop and select one "
        "product from each category. At the end, you will answer a few "
        "short questions about your choices."
    )

    st.write(
        "The study explores how different nudging techniques in an online fashion shop can "
        "encourage sustainable shopping choices. There are no right or wrong answers; "
        "please make your choices according to your own preferences."
    )

    st.info(
        "The shop is a research prototype. Product information, prices, "
        "materials and sustainability scores are simulated and may not "
        "correspond to real products. Sustainability scores are not verified "
        "environmental assessments."
    )

    if st.button("Continue", type="primary"):
        go_to("consent")


elif st.session_state.page == "consent":
    st.title("Consent")

    st.write(
        "Please read the following information carefully."
    )

    st.write(
        "1. Your participation in this study is voluntary "
    )

    st.write(
        "2. All information you provide in this study will be saved in an anonymous from (no personally identifiable information will be collected), "
        "will never be shared with any third party, and will be permanently deleted after the study is concluded."
    )

    st.write(
        "By continuing, you confirm that you are at least 18 years old and agree to participate in this study based on the information provided above."
        "and voluntarily agree to participate in this study."
    )

    consent = st.radio(
        "Please choose on option:",
        [
            "I agree to participate in the user study",
            "I do not agree to participate in the user study",
        ],
        index=None,
    )

    if st.button("Continue", type="primary"):
        if consent == "I agree to participate in the user study":
            st.session_state.consent_given = True
            go_to("interest")

        elif consent == "I do not agree to participate in the user study":
            st.session_state.consent_given = False
            st.info(
                "You have chosen not to participate. You may close this page."
            )

        else:
            st.warning(
                "Please select an option before continuing."
            )


elif st.session_state.page == "interest":
    st.title("About You")

    st.write(
        "Before you start, please answer a few short questions."
    )

    st.subheader("How old are you?")

    age = st.number_input(
        "Please enter your age:",
        min_value=18,
        max_value=100,
        value=None,
        step=1,
        placeholder="Enter your age",
    )

    st.subheader("What is your gender?")

    gender_options = [
        "Female",
        "Male",
        "Diverse",
        "Prefer not to say",
    ]

    selected_gender = st.radio(
        "Please select one answer:",
        gender_options,
        index=None,
    )

    st.subheader(
        "How interested are you in sustainable fashion?"
    )

    interest_options = [
        "Not interested at all",
        "Slightly interested",
        "Moderately interested",
        "Very interested",
        "Extremely interested",
    ]

    selected_interest = st.radio(
        "Please select one answer:",
        interest_options,
        index=None,
    )

    if st.button("Continue", type="primary"):
        if age is None:
            st.warning("Please enter your age.")

        elif selected_gender is None:
            st.warning("Please select your gender.")

        elif selected_interest is None:
            st.warning(
                "Please select your interest in sustainable fashion."
            )

        else:
            st.session_state.age = int(age)
            st.session_state.gender = selected_gender
            st.session_state.sustainability_interest = selected_interest

            go_to("shop")


elif st.session_state.page == "shop":
    df = pd.read_csv("Winter_Fashion_Dataset.csv")
    image_folder = "images"

    st.title("Online Fashion Shop")
    st.write("Choose one product from each category.")

    st.info(
        "**Sustainability Score:** The score ranges from 1 to 5. "
        "1 = less sustainable, 5 = more sustainable. These scores are "
        "simulated for this study."
    )

    products = [
        "Sweater",
        "Coat",
        "Beanie",
        "Boots",
    ]

    try:
        technique = assign_condition()
    except Exception:
        st.error(
            "The study condition could not be assigned. "
            "Please try again or contact the study administrator."
        )
        st.stop()

    valid_conditions = [
        "Control",
        "Labels",
        "Prioritization",
        "Framing",
    ]

    if technique not in valid_conditions:
        st.error(
            "The assigned study condition is invalid. "
            "Please contact the study administrator."
        )
        st.stop()

    st.progress(
        (st.session_state.step + 1) / len(products)
    )

    st.caption(
        f"Category {st.session_state.step + 1} of {len(products)}"
    )

    product = products[st.session_state.step]

    st.header(f"Choose your {product}")

    result = df[df["Category"] == product].copy()

    if result.empty:
        st.error(f"No products found for category: {product}")
        st.stop()

    result["Product_ID"] = result["Product_ID"].astype(str)

    highest_product = result.sort_values(
        by=["Sustainability", "Product_ID"],
        ascending=[False, True],
        kind="stable",
    ).iloc[0]

    highlight_product_id = str(highest_product["Product_ID"])

    if technique == "Prioritization":
        result = result.sort_values(
            by=["Sustainability", "Product_ID"],
            ascending=[False, True],
            kind="stable",
        )

    previous_selection = (
        st.session_state.selected_products.get(product)
    )

    columns = st.columns(3)

    for i, (_, row) in enumerate(result.iterrows()):
        product_id = str(row["Product_ID"])

        with columns[i % 3]:
            image_path = os.path.join(
                image_folder,
                f"{product_id}.png",
            )

            if os.path.exists(image_path):
                st.image(
                    image_path,
                    use_container_width=True,
                )
            else:
                st.caption(
                    f"Image not found: {image_path}"
                )

            if (
                technique == "Labels"
                and product_id == highlight_product_id
            ):
                st.subheader(str(row["Colour"]) + " 🌱")
            else:
                st.subheader(str(row["Colour"]))

            st.write(f"**Price:** €{row['Price_EUR']}")

            st.write(f"**Material:** {row['Material']}")

            st.write(
                f"**Sustainability Score:** "
                f"{row['Sustainability']}/5"
            )

            if (
                technique == "Framing"
                and product_id == highlight_product_id
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
                use_container_width=True,
            ):
                st.session_state.selected_products[
                    product
                ] = product_id

                st.rerun()

    st.divider()

    back_col, next_col = st.columns(2)

    with back_col:
        if st.session_state.step > 0:
            if st.button(
                "Back",
                use_container_width=True,
            ):
                st.session_state.step -= 1
                st.rerun()

    with next_col:
        if st.session_state.step < len(products) - 1:
            if st.button(
                "Next",
                type="primary",
                use_container_width=True,
            ):
                if product in st.session_state.selected_products:
                    st.session_state.step += 1
                    st.rerun()
                else:
                    st.warning(
                        "Please select a product first."
                    )

        else:
            if st.button(
                "Submit",
                type="primary",
                use_container_width=True,
            ):
                if product not in st.session_state.selected_products:
                    st.warning("Please select a product first.")

                elif st.session_state.response_saved:
                    go_to("completion")

                elif any(
                    category not in st.session_state.selected_products
                    for category in products
                ):
                    st.warning(
                        "Please select one product from every category."
                    )

                else:
                    selected = st.session_state.selected_products

                    response = {
                        "participant_id": (
                            st.session_state.participant_id
                        ),
                        "assigned_condition": (
                            st.session_state.assigned_condition
                        ),
                        "age": st.session_state.age,
                        "gender": st.session_state.gender,
                        "sweater_id": selected["Sweater"],
                        "coat_id": selected["Coat"],
                        "beanie_id": selected["Beanie"],
                        "boot_id": selected["Boots"],
                        "sustainability_interest": (
                            st.session_state.sustainability_interest
                        ),
                    }

                    try:
                        existing_response = (
                            supabase.table("study_responses")
                            .select("participant_id")
                            .eq(
                                "participant_id",
                                st.session_state.participant_id,
                            )
                            .execute()
                        )

                        if existing_response.data:
                            st.error(
                                "A response for this participant has already been saved."
                            )
                        else:
                            supabase.table("study_responses").insert(
                                response,
                                returning="minimal",
                            ).execute()

                            st.session_state.response_saved = True
                            go_to("completion")

                    except Exception as e:
                        st.error(
                            f"Error saving response: {e}"
                        )


elif st.session_state.page == "completion":
    st.title("Thank You for Participating!")

    st.success(
        "Your responses have been submitted successfully."
    )

    st.write(
        "Thank you for taking the time to participate in this study. "
        "Your responses are valuable for this research."
    )

    st.write(
        "You may now close this page."
    )
