import streamlit as st
import numpy as np
# import matplotlib.pyplot as plt
import plotly.graph_objects as go

# For clickable plotly events:
from streamlit_plotly_events import plotly_events

# # For matplotlib plots:
# from matplotlib.backends.backend_agg import RendererAgg
# _lock = RendererAgg.lock


def main(sorted_results):
    """
    Plot sorted probability bar chart
    """

    # Add the bars to the chart in the same order as the highlighted
    # teams list. Otherwise by default the bars would be added in the
    # order of sorted rank, and adding a new highlighted team could
    # change the colours of the existing teams.
    # (Currently removing a team does shuffle the colours but I don't
    # see an easy fix to that.)
    # Make the ordered list of things to add:
    highlighted_teams_list = st.session_state['hb_teams_input']
    # highlighted_teams_list = np.append(['-', '\U00002605' + ' (Benchmark)'], highlighted_teams_list)
    # Store the colours used in here:
    highlighted_teams_colours = st.session_state['highlighted_teams_colours']

    fig = go.Figure()
    for i, leg_entry in enumerate(highlighted_teams_list):
        # Take the subset of the big dataframe that contains the data
        # for this highlighted team:
        results_here = sorted_results[
            sorted_results['HB team'] == leg_entry]
        # Choose the colour of this bar:
        colour = highlighted_teams_colours[leg_entry]
        # Add bar(s) to the chart for this highlighted team:
        fig.add_trace(go.Bar(
            x=results_here['Sorted rank'],
            y=results_here['Probability_perc'],
            # Extra data for hover popup:
            customdata=np.stack([
                results_here['Stroke team'],
                results_here['Thrombolyse_str'],
                # results_here['Benchmark']
                ], axis=-1),
            # Name for the legend:
            name=leg_entry,
            # Set bars colours:
            marker=dict(color=colour)
            ))

    # Figure title:
    # Change axis:
    fig.update_yaxes(range=[0.0, 100.0])
    xmax = sorted_results.shape[0]
    fig.update_xaxes(range=[0.0, xmax+1])
    fig.update_layout(xaxis=dict(
        tickmode='array',
        tickvals=np.arange(0, sorted_results.shape[0], 10),
        ))

    # Update titles and labels:
    fig.update_layout(
        # title='Effect on probability by feature',
        xaxis_title=f'Rank out of {sorted_results.shape[0]} stroke teams',
        yaxis_title='Probability of giving<br>thrombolysis',
        legend_title='Highlighted team'
        )

    # Hover settings:
    # Make it so cursor can hover over any x value to show the
    # label of the survival line for (x,y), rather than needing to
    # hover directly over the line:
    fig.update_layout(hovermode='x')
    # Update the information that appears on hover:
    fig.update_traces(
        hovertemplate=(
            # Stroke team:
            '%{customdata[0]}' +
            '<br>' +
            # Probability to two decimal places:
            '%{y:>.2f}%' +
            '<br>' +
            # Yes/no whether to thrombolyse:
            'Thrombolysis: %{customdata[1]}' +
            '<br>' +
            # Yes/no whether it's a benchmark team:
            # '%{customdata[2]}'
            '<extra></extra>'
            )
        )

    # Add horizontal line at prob=0.5, the decision to thrombolyse:
    fig.add_hline(y=50.0, line=dict(color='black'))
    # Update y ticks to match this 50% line:
    fig.update_layout(yaxis=dict(
        tickmode='array',
        tickvals=[0, 20, 40, 50, 60, 80, 100],
        ))

    # Reduce size of figure by adjusting margins:
    fig.update_layout(
        margin=dict(    
            # l=50,
            # r=50,
            b=80,
            t=20,
            # pad=4
        ),
        height=250
        )
    # fig.update_xaxes(automargin=True)

    # Write to streamlit:
    # # Non-interactive version:
    # st.plotly_chart(fig, use_container_width=True)

    # Clickable version:
    # Write the plot to streamlit, and store the details of the last
    # bar that was clicked:
    selected_bar = plotly_events(fig, click_event=True, key='bars',
        override_height=250)#, override_width='50%')
    try:
        # Pull the details out of the last bar that was changed
        # (moved to or from the "highlighted" list due to being
        # clicked on) out of the session state:
        last_changed_bar = st.session_state['last_changed_bar']
    except KeyError:
        # Invent some nonsense. It doesn't matter whether it matches
        # the default value of selected_bar before anything is clicked.
        last_changed_bar = [0]
    callback_bar(selected_bar, last_changed_bar, 'last_changed_bar', sorted_results)
    # return selected_bar


def callback_bar(selected_bar, last_changed_bar, last_changed_str, sorted_results):
    """
    # When the script is re-run, this value of selected bar doesn't
    # change. So if the script is re-run for another reason such as
    # a streamlit input widget being changed, then the selected bar
    # is remembered and it looks indistinguishable from the user
    # clicking the bar again. To make sure we only make updates if
    # the user actually clicked the bar, compare the current returned
    # bar details with the details of the last bar *before* it was
    # changed.
    # When moved to or from the highlighted list, the bar is drawn
    # as part of a different trace and so its details such as
    # curveNumber change.
    # When the user clicks on the same bar twice in a row, we do want
    # the bar to change. For example, a non-highlighted bar might have
    # curveNumber=0, then when clicked changes to curveNumber=1.
    # When clicked again, the last_changed_bar has curveNumber=0,
    # but selected_bar has curveNumber=1. The bar details have changed
    # and so the following loop still happens despite x and y being
    # the same.
    """
    if selected_bar != last_changed_bar:
        # If the selected bar doesn't match the last changed bar,
        # then we need to update the graph and store the latest
        # clicked bar.
        try:
            # If a bar has been clicked, then the following line
            # will not throw up an IndexError:
            rank_selected = selected_bar[0]['x']
            # Find which team this is:
            team_selected = sorted_results['Stroke team'].loc[
                sorted_results['Sorted rank'] == rank_selected].values[0]
            # Copy the current highlighted teams list
            highlighted_teams_list_updated = \
                st.session_state['highlighted_teams']
            # Check if the newly-selected team is already in the list.
            if team_selected in highlighted_teams_list_updated:
                # Remove this team from the list.
                highlighted_teams_list_updated.remove(team_selected)
            else:
                # Add the newly-selected team to the list.
                highlighted_teams_list_updated.append(team_selected)
            # Add this new list to the session state so that
            # streamlit can access it immediately on the next re-run.
            st.session_state['highlighted_teams_with_click'] = \
                highlighted_teams_list_updated

            # Keep a copy of the bar that we've just changed,
            # and put it in the session state so that we can still
            # access it once the script is re-run:
            st.session_state[last_changed_str] = selected_bar.copy()

            # Re-run the script to get immediate feedback in the
            # multiselect input widget and the graph colours:
            st.experimental_rerun()

        except IndexError:
            # Nothing has been clicked yet, so don't change anything.
            pass


def plot_sorted_probs_matplotlib(sorted_results):

    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot()
    x_chart = range(len(sorted_results))
    ax.bar(x_chart, sorted_results['Probability'], width=0.5)
    ax.plot([0, len(sorted_results)], [0.5, 0.5], c='k')
    ax.axes.get_xaxis().set_ticks([])
    ax.set_xlabel('Stroke team')
    ax.set_ylabel('Probability of giving patient thrombolysis')

    ax.set_ylim(0, 1)
    st.pyplot(fig)
    plt.close(fig)
