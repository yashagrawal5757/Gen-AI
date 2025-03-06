# Imports
import os
import streamlit as st
import json
#from constants import *
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser



# Fetch API keys from Streamlit secrets or import from constants.py 
#below is required only for local execution -> uncomment next two lines when running locally
#OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
#LANGCHAIN_API_KEY = st.secrets["LANGCHAIN_API_KEY"]

# Connect API keys
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
# Tracing on Langsmith
os.environ['LANGCHAIN_TRACING'] = "true" 
os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY

# Create OpenAI LLM object
llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
output_parser = StrOutputParser()  # For cleaning output

# Streamlit UI
st.title("AI Powered Personal Finance Assistant Chatbot")
st.markdown(f"""
    <style>
        @keyframes glitter {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}

        .glitter-text {{
            font-size: 20px;
            font-weight: bold;
            background: linear-gradient(45deg, #FFD700, #FFB6C1, #C0C0C0, #FFD700);
            background-size: 400% 400%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: glitter 3s infinite linear;
        }}
    </style>
    <p class="glitter-text">Powered by {llm.model_name} model</p>
""", unsafe_allow_html=True)

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
savings = st.number_input("Total Current Savings:", min_value=0, step=100)
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
prompt_profiling = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a financial advisor. Your task is to analyze the user's financial profile based strictly on the provided data. "
     "Do not make assumptions, generate additional numbers, or modify values. If a value is missing, explicitly state that instead of estimating it. "
     "The financial data is provided in a structured JSON format. Parse it properly and ensure all calculations strictly use these values."
     "\n\n### Formatting Guidelines:"
     "\n- Use proper spacing between numbers and words."
     "\n- Do not use `_` for emphasis as it can cause unwanted italicization."
     "\n- No unwanted italicization required." 
     "\n\nAfter summarizing the user's financial profile, provide insights on:"
     "- Whether their expenses are too high in comparison to their income."
     "- If they are saving enough based on standard recommendations (e.g., 20 percent of income should go toward savings)."
     "- Whether they are managing debt responsibly, including debt-to-income ratio considerations."
     "- Suggestions for improvements based on their goals and financial health."
     "**Savings Rate Calculation:**\n"
     "- **Formula:** Monthly Savings = (Income - Total Expenses).\n"
     "- **Savings Rate Formula:** (Monthly Savings / Income) × 100.\n"
    ),
    ("user", 
     "Here is the user's financial profile in JSON format:\n```json\n{financial_data_str}\n```\n"
     "Summarize this data exactly as provided, then analyze it based on the criteria mentioned above. "
     "Follow the formatting guidelines strictly."
    )
])


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
    
    # Store the financial data in session state for reuse
    st.session_state["financial_data_str"] = financial_data_str
    

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

        # Ensure financial data from session state is used
        financial_data_str = st.session_state.get("financial_data_str", "{}")  # Use "{}" if missing

        # Ensure analyzed response is used when relevant
        analyzed_response = st.session_state.get("analyzed_response", "No prior analysis found.")
        
        if advice_option == "Budget Breakdown":
            prompt_budget = ChatPromptTemplate.from_messages([ 
                    ("system", 
                        "You are a financial advisor. The user seeks help managing their budget. "
                        "Keep the language simple, provide personalized numbers, and ensure the response follows a structured breakdown.\n\n"
                        "\n\n### Formatting Guidelines:"
                        "\n- Use proper spacing between numbers and words."
                        "\n- Do not use `_` for emphasis as it can cause unwanted italicization."
                        "\n- No unwanted italicization required." 
                        "### Budget Breakdown Must Include:\n"
                        "- **Expense Categorization:** Classify expenses into **Fixed (e.g., rent, utilities)** and **Variable (e.g., food, entertainment).**\n"
                        "- **Expense Prioritization:** Rank each expense as **High, Medium, or Low Priority** and suggest reductions for non-essentials.\n"
                        "- **Expense Percentage Analysis:** Calculate what **percentage of total income** each category consumes.\n"
                        "- **Savings Evaluation:** Assess if savings align with financial guidelines (**20% of income**).\n"
                        "- **Emergency Fund Check:** Determine if the user has **at least 3-6 months of expenses saved** and suggest adjustments if needed.\n"
                        "- **Custom Budgeting Strategy Based on Financial Goals:**\n"
                        "   - If goal is **debt repayment**, suggest an aggressive pay-off strategy.\n"
                        "   - If goal is **home purchase**, recommend high-interest savings accounts.\n"
                        "   - If goal is **retirement savings**, suggest tax-advantaged investment options.\n"
                        "- **Actionable Steps:** Provide a clear plan on how to improve budgeting habits and optimize financial stability.\n"
                        "**Savings Rate Calculation:**\n"
                        "- **Formula:** Monthly Savings = (Income - Total Expenses).\n"
                        "- **Savings Rate Formula:** (Monthly Savings / Income) × 100.\n"
                    ),
                    ("user", 
                        "Using the following financial profile and prior analysis, create a structured and actionable budget breakdown:\n\n"
                        "### User's Financial Profile\n"
                        "```\n{financial_data_str}\n```\n\n"
                        "### Previous Analysis\n"
                        "```\n{analyzed_response}\n```\n\n"
                        "Follow the formatting guidelines strictly."
                    )
                ])

            chain_budget = prompt_budget | llm | output_parser
            response_budget = chain_budget.invoke({"financial_data_str": financial_data_str,
                                                   "analyzed_response": analyzed_response})
            st.write(response_budget)
            st.session_state["detailed_feedback"] = response_budget
        
        # Debt Repayment Strategy
        elif advice_option == "Debt Repayment Strategy":
            prompt_debt = ChatPromptTemplate.from_messages([ 
            ("system", 
                "You are a financial advisor. The user is seeking advice on paying off their debt. "
                "Keep the language simple and provide a structured, step-by-step debt repayment plan. "
                "Ensure that numbers are personalized based on their financial data.\n\n"
                "\n\n### Formatting Guidelines:"
                "\n- Use proper spacing between numbers and words."
                "\n- Do not use `_` for emphasis as it can cause unwanted italicization."
                "\n- No unwanted italicization required." 
                "### Debt Repayment Strategy Must Include:\n"
                "- **Debt Categorization:** Identify all debt types and list their balances & interest rates.\n"
                "- **Optimal Payoff Method:** Suggest whether they should use the **Avalanche (high-interest first)** or **Snowball (smallest first)** method.\n"
                "- **Monthly Payment Breakdown:** Recommend how much they should allocate towards debt each month.\n"
                "- **Debt-Free Timeline:** Estimate when they will be debt-free based on current income and expenses.\n"
                "- **Impact on Credit Score:** Briefly explain how different strategies affect credit standing.\n"
                "- **Alternative Options:** If applicable, suggest **loan consolidation, refinancing, or balance transfers**.\n"
            ),
            ("user", 
                "Using the following financial profile and previous analysis, create a comprehensive debt repayment plan:\n\n"
                "### User's Financial Profile\n"
                "```\n{financial_data_str}\n```\n\n"
                "### Previous Analysis\n"
                "```\n{analyzed_response}\n```\n\n"
                "Follow the formatting guidelines strictly."
            )
    ])
            chain_debt = prompt_debt | llm | output_parser
            response_debt = chain_debt.invoke({"financial_data_str": financial_data_str,
                                                   "analyzed_response": analyzed_response})
            st.write(response_debt)
            st.session_state["detailed_feedback"] = response_debt
        
        # Savings Milestone Suggestion
        elif advice_option == "Savings Milestone Suggestion":
            prompt_savings = ChatPromptTemplate.from_messages([ 
                ("system", 
                    "You are a financial advisor. The user seeks guidance on setting savings milestones. "
                    "Use clear, realistic targets and ensure numbers are personalized.\n\n"
                    "\n\n### Formatting Guidelines:"
                    "\n- Use proper spacing between numbers and words."
                    "\n- Do not use `_` for emphasis as it can cause unwanted italicization."
                    "\n- No unwanted italicization required." 
                    "### Savings Plan Must Include:\n"
                    "- **Short-Term Goals (6-12 months):** Emergency fund, vacation, short-term needs.\n"
                    "- **Mid-Term Goals (1-5 years):** Home purchase, major purchases, tuition.\n"
                    "- **Long-Term Goals (5+ years):** Retirement, financial independence, investments.\n"
                    "- **Savings Target Calculation:** Recommend how much to save each month to meet these goals.\n"
                    "- **Best Savings Methods:** Compare **high-yield savings, CDs, Roth IRAs, 401(k), and investments**.\n"
                    "- **Automated Savings Strategy:** Suggest tools like auto-deposits, budgeting apps, and employer-match contributions.\n"
                ),
                ("user", 
                    "Based on the user's financial data and goals, create a structured savings milestone plan:\n\n"
                    "### User's Financial Profile\n"
                    "```\n{financial_data_str}\n```\n\n"
                    "### Previous Analysis\n"
                    "```\n{analyzed_response}\n```\n\n"
                    "Follow the formatting guidelines strictly."
        )
    ])
            chain_savings = prompt_savings | llm | output_parser
            response_savings = chain_savings.invoke({"financial_data_str": financial_data_str,
                                                   "analyzed_response": analyzed_response})
            st.write(response_savings)
            st.session_state["detailed_feedback"] = response_savings

        # Investment Advice
        elif advice_option == "Investment Advice":
            prompt_investment = ChatPromptTemplate.from_messages([ 
                ("system", 
                    "You are a financial advisor. The user is seeking investment guidance based on their financial profile. "
                    "Ensure investment suggestions align with their **risk tolerance, financial goals, and current savings.**\n\n"
                    "\n\n### Formatting Guidelines:"
                    "\n- Use proper spacing between numbers and words."
                    "\n- Do not use `_` for emphasis as it can cause unwanted italicization."
                    "\n- No unwanted italicization required." 
                    "### Investment Strategy Must Include:\n"
                    "- **Investment Readiness Check:** Determine if the user has sufficient savings before investing.\n"
                    "- **Risk-Based Investment Suggestions:** Conservative (bonds, CDs), Balanced (index funds, ETFs), Aggressive (stocks, crypto).\n"
                    "- **Diversification Plan:** Recommend allocation percentages across different asset classes.\n"
                    "- **Retirement Planning:** Suggest **401(k), Roth IRA, and HSA accounts.**\n"
                    "- **Tax-Advantaged Investments:** Explain tax benefits of certain investments.\n"
                ),
                ("user", 
                    "Using the following financial profile and risk tolerance, create a personalized investment plan:\n\n"
                    "### User's Financial Profile\n"
                    "```\n{financial_data_str}\n```\n\n"
                    "### Previous Analysis\n"
                    "```\n{analyzed_response}\n```\n\n"
                    "Follow the formatting guidelines strictly."
                )
    ])
            chain_investment = prompt_investment | llm | output_parser
            response_investment = chain_investment.invoke({
                                    "financial_data_str": financial_data_str,
                                    "analyzed_response": analyzed_response
                                                            })
            st.write(response_investment)
            st.session_state["detailed_feedback"] = response_investment

        # Emergency Fund Calculation
        elif advice_option == "Emergency Fund Calculation":
            prompt_emergency = ChatPromptTemplate.from_messages([ 
                ("system", 
                    "You are a financial advisor. The user is seeking emergency fund guidance. "
                    "Ensure your calculations are **based on their expenses and current savings.**\n\n"
                    "\n\n### Formatting Guidelines:"
                    "\n- Use proper spacing between numbers and words."
                    "\n- Do not use `_` for emphasis as it can cause unwanted italicization."
                    "\n- No unwanted italicization required." 
                    "### Emergency Fund Plan Must Include:\n"
                    "- **Months of Expenses Covered:** Calculate how many months the current fund lasts.\n"
                    "- **Standard Benchmark:** Compare against the **recommended 3-6 month savings rule.**\n"
                    "- **Monthly Contribution Suggestion:** Estimate how much to save monthly to meet the goal.\n"
                    "- **Best Account Type:** Suggest storing the fund in **high-yield savings, money market, or liquid assets.**\n"
                ),
                ("user", 
                    "Based on their expenses and savings, calculate how much they should save for an emergency fund:\n\n"
                    "### User's Financial Profile\n"
                    "```\n{financial_data_str}\n```\n\n"
                    "### Previous Analysis\n"
                    "```\n{analyzed_response}\n```\n\n"
                    "Follow the formatting guidelines strictly."
                )
    ])
            chain_emergency = prompt_emergency | llm | output_parser
            response_emergency = chain_emergency.invoke({
                                    "financial_data_str": financial_data_str,
                                    "analyzed_response": analyzed_response
                                                        })
            st.write(response_emergency)
            st.session_state["detailed_feedback"] = chain_emergency

        # Financial Health Report
        elif advice_option == "Financial Health Report":
            prompt_health = ChatPromptTemplate.from_messages([ 
                ("system", 
                    "You are a financial advisor. The user is seeking a comprehensive financial health assessment. "
                    "Provide a structured report based on their financial data.\n\n"
                    "\n\n### Formatting Guidelines:"
                    "\n- Use proper spacing between numbers and words."
                    "\n- Do not use `_` for emphasis as it can cause unwanted italicization."
                    "\n- No unwanted italicization required." 
                    "### Financial Health Report Must Include:\n"
                    "- **Overall Financial Score (1-10):** Assign a score based on their income, expenses, savings, and debt levels.\n"
                    "- **Debt-to-Income (DTI) Ratio Analysis:** Calculate their DTI ratio and assess if it's in a healthy range.\n"
                    "- **Savings Rate Evaluation:** Compare the user's savings rate to financial guidelines (e.g., saving at least 20% of income).\n"
                    "- **Expense Optimization:** Identify high spending categories and suggest reductions for discretionary expenses.\n"
                    "- **Emergency Fund Status:** Check if they have 3-6 months of expenses saved and recommend adjustments if needed.\n"
                    "- **Retirement Readiness:** Determine if they are contributing adequately to retirement plans (401k, Roth IRA, etc.).\n"
                    "- **Investment Readiness:** Assess if they have a strong financial foundation for investing and suggest asset allocation.\n"
                    "- **Personalized Recommendations:** Provide a **step-by-step action plan** to improve financial health.\n"
                ),
                ("user", 
                    "Using the following financial profile and prior analysis, create a structured financial health report:\n\n"
                    "### User's Financial Profile\n"
                    "```\n{financial_data_str}\n```\n\n"
                    "### Previous Analysis\n"
                    "```\n{analyzed_response}\n```\n\n"
                    "Follow the formatting guidelines strictly."
                )
    ])
            chain_health = prompt_health | llm | output_parser
            response_health = chain_health.invoke({
                                "financial_data_str": financial_data_str,
                                "analyzed_response": analyzed_response
                                                })
            st.write(response_health)
            st.session_state["detailed_feedback"] = response_health
