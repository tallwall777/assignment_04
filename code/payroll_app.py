"""
payroll_app.py — the weekly payroll, for someone who has never opened a terminal.

Every Friday the office manager at Salt City Coffee exports the week's timesheet
from the point-of-sale system. This page turns it into a paycheck table and the
CSV the online payroll provider imports — without the manager touching pandas.

The app is mostly *assembly*: the roster is loaded from data/, the upload comes
from the page, and one call to `build_payroll` does all the work. What the page
adds is what a manager needs to trust the numbers: totals, a loud warning about
anything the pipeline could not match, the full lineage table, and the download.

Run it:  Run and Debug -> "Streamlit Run: Current File"   (see README Reference #1)
Test it: pytest tests/test_pipeline.py -k app
"""

# --- The page ---------------------------------------------------------------------
#
# No scaffolding. Every function this page needs already exists in the payroll
# package, and every widget it needs you used in Assignment 03. README Step 8 has
# the exact widgets, keys and labels; the tests in tests/test_pipeline.py -k app
# check them.
#
# The shape, in words:
#
#   title and a sentence of instructions
#   roster  <- load_employees()                      (fixed; not uploaded)
#   upload  <- st.file_uploader, key="timesheet"     (returns None until chosen)
#   if there is an upload:
#       timesheet <- load_timesheet(upload)
#       payroll   <- build_payroll(timesheet, roster)   one call does all the work
#       the pay period (payroll_date) as a subheader
#       four st.metric cards in st.columns(4) — totals are .sum() on a Series,
#           counts are len() of a boolean-indexed frame
#       st.warning naming the unmatched employee_ids, or st.success if none
#       st.dataframe(payroll) — the lineage table, raw and computed side by side
#       st.download_button, key="download": payroll_export(payroll).to_csv(index=False)
#
# What the page does NOT do: arithmetic on rows, cleaning, merging. If you find
# yourself writing a loop or an apply here, that logic belongs in the package.
import streamlit as st
from payroll import (
    load_employees,
    load_timesheet,
    build_payroll,
    payroll_export,
)

# --- Page Title & Instructions ----------------------------------------------------

st.title("Weekly Payroll")
st.write("Upload the week's timesheet to generate the payroll table and provider CSV.")

# --- Load the fixed roster --------------------------------------------------------

roster = load_employees()

# --- Timesheet Upload -------------------------------------------------------------

upload = st.file_uploader("Timesheet File", key="timesheet")

if upload is not None:
    # Load → Build Payroll
    timesheet = load_timesheet(upload)
    payroll = build_payroll(timesheet, roster)

    # --- Pay Period ---------------------------------------------------------------
    st.subheader(f"Pay Period: {payroll['payroll_date'].iloc[0]}")

    # --- Metrics ------------------------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Employees paid", len(payroll[payroll["pay_type"] != "unmatched"]["employee_id"].unique()))
    col2.metric("Total hours", payroll["hours_worked"].sum())
    col3.metric("Total gross pay", f"${payroll['gross_pay'].sum():,.2f}")
    col4.metric("Overtime weeks", len(payroll[payroll["pay_type"] == "overtime"]))

    # --- Unmatched Warning --------------------------------------------------------
    unmatched = payroll[payroll["pay_type"] == "unmatched"]["employee_id"]

    if len(unmatched) > 0:
        st.warning(f"Unmatched employee IDs: {', '.join(str(x) for x in unmatched)}")
    else:
        st.success("All employees matched to the roster.")

    # --- Lineage Table ------------------------------------------------------------
    st.dataframe(payroll)

    # --- Download Provider CSV ----------------------------------------------------
    csv_data = payroll_export(payroll).to_csv(index=False)
    st.download_button(
        "Download Provider CSV",
        csv_data,
        file_name="payroll.csv",
        mime="text/csv",
        key="download",
    )
