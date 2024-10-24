# Imports
import os
import streamlit as st
import json
from constants import *
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Connect API keys
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
# Tracing on Langsmith
os.environ['LANGCHAIN_TRACING'] = "true" 
os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY

# Create OpenAI LLM object
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
output_parser = StrOutputParser()  # For cleaning output

# Streamlit UI
st.title("Personal Finance Assistant Chatbot")
st.write(f"Powered by {llm.model_name} model")

st.write("Provide necessary financial information about yourself. Mention the amount in dollars but don't mention the symbol.")

# ----------------------------------------------------------------------------- 
# Section 1: Monthly Income
income = st.number_input("Monthly Income after taxes", min_value=0, step=100)

# Section 2: Monthly Expenses
st.subheader("Monthly Expenses")
housing = st.number_input("Housing (rent/mortgage):", min_value=0, step=100)
utilities = st.number_input("Utilities (electricity, water, etc.):", min_value=0, step=100)
groceries = st.number_input("Groceries:", min_value=0, step=100)
entertainment = st.number_input("Entertainment:", min_value=0, step=100)
transportation = st.number_input("Transportation (car, bus, etc.):", min_value=0, step=100)
other_expenses = st.number_input("Other Expenses:", min_value=0, step=100)

# Section 3: Debt Information
st.subheader("Debt Information")
has_debt = st.radio("Do you have any debt?", ("Yes", "No"))
if has_debt == "Yes":
    num_debts = st.number_input("How many types of debt do you have?", min_value=1, step=1)
    debts = []
    for i in range(num_debts):
        st.write(f"Debt {i+1}:")
        debt_type = st.selectbox(f"Debt Type {i+1}", ["Credit Card", "Student Loan", "Mortgage", "Other"], key=f"type_{i}")
        debt_balance = st.number_input(f"{debt_type} Balance:", min_value=0, step=100, key=f"balance_{i}")
        interest_rate = st.number_input(f"Interest Rate for {debt_type} (%):", min_value=0.0, step=0.1, key=f"rate_{i}")

        # Store the debt information in the debts list
        debts.append({
            "debt_type": debt_type,
            "debt_balance": debt_balance,
            "interest_rate": interest_rate,
        })

# Section 4: Savings and Investments
st.subheader("Savings and Investments")
savings = st.number_input("Current Savings:", min_value=0, step=100)
investments = st.text_area("Describe your current investments (if any):")

# Section 5: Financial Goals
st.subheader("Your Financial Goals")
goals = st.multiselect("Select your financial goals:", 
                       ["Building an Emergency Fund", "Saving for Retirement", "Paying off Debt", 
                        "Investing for the Future", "Other"])
other_goals = st.text_input("If 'Other', please specify your goal:")

# Section 6: Risk Tolerance for Investments
st.subheader("Investment Risk Tolerance")
risk_tolerance = st.radio("How would you describe your risk tolerance?", 
                          ["Conservative", "Balanced", "Aggressive"])

# Section 7: Emergency Fund
st.subheader("Emergency Fund")
emergency_fund = st.radio("Do you have an emergency fund?", ("Yes", "No"))
if emergency_fund == "Yes":
    months_covered = st.number_input("How many months of living expenses does it cover?", min_value=0, step=1)

# Section 8: Time Frame for Savings Goals
st.subheader("Time Frame for Savings Goals")
time_frame = st.selectbox("Select the time frame for your savings goals:", 
                          ["6 months", "1 year", "2 years", "5 years"])

# Section 9: Miscellaneous Financial Information
st.subheader("Additional Information")
misc_info = st.text_area("Is there anything else you'd like to share about your financial situation?")

# -------------------------------------------------------------------------
# Store values to pass to prompt template
financial_data = {
    "income": income,
    "expenses": {
        "housing": housing,
        "utilities": utilities,
        "groceries": groceries,
        "entertainment": entertainment,
        "transportation": transportation,
        "other_expenses": other_expenses
    },
    "debts": debts if has_debt == "Yes" else [],
    "savings": savings,
    "investments": investments,
    "financial_goals": goals,
    "risk_tolerance": risk_tolerance,
    "emergency_fund": {
        "exists": emergency_fund,
        "months_covered": months_covered if emergency_fund == "Yes" else None
    },
    "time_frame": time_frame,
    "misc_info": misc_info
}

# --------------------------------------------------------------------------

#serialize dictionary so that it can be passed in prompt templates
financial_data_str = json.dumps(financial_data, indent=4)

# Create the profiling prompt template
prompt_profiling = ChatPromptTemplate.from_messages ( 
    [
        ("system", 
         "You are a financial advisor. Provide a summary of the user's financial profile based on the data provided below. Don't use special characters so that it doesn't mess with the formatting of response. "
         "In addition, offer quick insights or suggestions such as: "
         "- Whether their expenses are too high in comparison to their income. "
         "- If they are saving enough based on standard recommendations (e.g., 20 percent of income should go toward savings). "
         "- Whether they are managing debt responsibly, including debt-to-income ratio considerations. "
         "- Suggestions for improvements based on their goals and financial health."
        ),
        ("user", "Summarize & analyze the following financial profile: {{financial_data_str}}")
    ]
)

# Use LLM Chain to execute the profiling prompt
chain1 = prompt_profiling | llm | output_parser

# ------------------------------------------------------------------------------------------
# Since streamlit reruns app, if you click 2nd radio button, we use st.session_state as memory
# It will store if finances were analyzed before or not, what is current radio selection
if "analyzed_response" not in st.session_state:
    st.session_state["analyzed_response"] = None
if "selected_advice" not in st.session_state:
    st.session_state["selected_advice"] = None
if "detailed_feedback" not in st.session_state:
    st.session_state["detailed_feedback"] = None

# Button for analyzing finances
if st.button("Analyze my finances"):
    response1 = chain1.invoke({"financial_data_str": financial_data_str})
    st.session_state["analyzed_response"] = response1    # Mark as analyzed
    st.session_state["detailed_feedback"] = None  
    # Reset detailed feedback because if a 2nd radio button is clicked, we want a fresh response to be generated

if st.session_state["analyzed_response"]:
    st.write(st.session_state["analyzed_response"])

# Show detailed feedback options only if analysis is complete
if st.session_state["analyzed_response"]:
    #Show 2nd prompt only when previously analysis is done
    st.subheader("Select the type of personalized advice you want:")

    # Use session state to remember the radio button selection
    st.session_state["selected_advice"] = st.radio(
        "Choose one of the following:",
        ("Budget Breakdown", "Debt Repayment Strategy", "Savings Milestone Suggestion", 
            "Investment Advice", "Emergency Fund Calculation", "Financial Health Report")
    )
    # User's radio button selection is stored in session state - streamlit remembers user's choice
    
    # If the user selected an advice option, and clicked on the "Get Detailed Feedback" button
    if st.session_state["selected_advice"] is not None and st.button("Get Detailed Feedback"):
        advice_option = st.session_state["selected_advice"] #use current radio selection to give response

        if advice_option == "Budget Breakdown":
            prompt_budget = ChatPromptTemplate.from_messages([ 
                ("system", "You are a financial advisor. The user seeks help managing their budget. Keep the language simple. Provide personalized numbers in response"),
                ("user", "Provide a detailed breakdown of their budget based on this financial profile: {{financial_data_str}}. "
                        "Offer suggestions on areas to reduce expenses and how much they should aim to save each month.")
            ])
            chain_budget = prompt_budget | llm | output_parser
            response_budget = chain_budget.invoke({"financial_data_str": financial_data_str})
            st.write(response_budget)
            st.session_state["detailed_feedback"] = response_budget
        
        # Debt Repayment Strategy
        elif advice_option == "Debt Repayment Strategy":
            prompt_debt = ChatPromptTemplate.from_messages([ 
                ("system", "You are a financial advisor. The user is seeking advice on paying off their debt.Keep the language simple. Provide personalized numbers in response"),
                ("user", "Based on the financial data: {{financial_data_str}}, provide an optimal debt repayment plan.")
            ])
            chain_debt = prompt_debt | llm | output_parser
            response_debt = chain_debt.invoke({"financial_data_str": financial_data_str})
            st.write(response_debt)
            st.session_state["detailed_feedback"] = response_debt
        
        # Savings Milestone Suggestion
        elif advice_option == "Savings Milestone Suggestion":
            prompt_savings = ChatPromptTemplate.from_messages([ 
                ("system", "You are a financial advisor. The user seeks help with savings goals.Provide personalized numbers in response"),
                ("user", "Based on their financial data and goals: {{financial_data_str}}, provide a savings milestone plan. "
                        "Suggest monthly savings targets to reach their long-term goals.")
            ])
            chain_savings = prompt_savings | llm | output_parser
            response_savings = chain_savings.invoke({"financial_data_str": financial_data_str})
            st.write(response_savings)
            st.session_state["detailed_feedback"] = response_savings

        # Investment Advice
        elif advice_option == "Investment Advice":
            prompt_investment = ChatPromptTemplate.from_messages([ 
                ("system", "You are a financial advisor. The user is looking for investment advice.Provide personalized numbers in response"),
                ("user",  "Based on their financial profile and risk tolerance: {{financial_data_str}}, "
                        "offer basic investment advice. Suggest types of investments and general allocations based on their risk appetite.")
            ])
            chain_investment = prompt_investment | llm | output_parser
            response_investment = chain_investment.invoke({"financial_data_str": financial_data_str})
            st.write(response_investment)
            st.session_state["detailed_feedback"] = response_investment

        # Emergency Fund Calculation
        elif advice_option == "Emergency Fund Calculation":
            prompt_emergency = ChatPromptTemplate.from_messages([ 
                ("system", "You are a financial advisor. The user is seeking advice on their emergency fund.Provide personalized numbers in response"),
                ("user", "Based on their expenses and savings: {{financial_data_str}}, calculate how much they should save for an emergency fund. "
                            "Advise on if current fund is okay. Provide actionable steps to reach this goal.")
            ])
            chain_emergency = prompt_emergency | llm | output_parser
            response_emergency = chain_emergency.invoke({"financial_data_str": financial_data_str})
            st.write(response_emergency)
            st.session_state["detailed_feedback"] = chain_emergency

        # Financial Health Report
        elif advice_option == "Financial Health Report":
            prompt_health = ChatPromptTemplate.from_messages([ 
                ("system", "You are a financial advisor. The user is seeking a comprehensive financial health report. Provide personalized numbers in response"),
                ("user", "Based on their overall financial profile: {{financial_data_str}}, provide a detailed financial health report. "
                        "Include an analysis of their debt-to-income ratio, savings adequacy, and overall financial standing.")
            ])
            chain_health = prompt_health | llm | output_parser
            response_health = chain_health.invoke({"financial_data_str": financial_data_str})
            st.write(response_health)
            st.session_state["detailed_feedback"] = response_health
