from __future__ import annotations

import io

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from rtd_analyzer.data_processing import (
    channel_columns,
    compute_transition_zones,
    load_measurements,
    normalize_dimensionless,
    prepare_experiment_window,
)


def _render_author_footer() -> None:
    st.markdown("---")
    st.caption("Autor: Mateusz Łatka | Indeks: 305382 | ml305382@student.polsl.pl")


def _plot_curves(
    df: pd.DataFrame,
    channels: list[str],
    ylabel: str,
    show_limits: bool = False,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 5))
    for channel in channels:
        ax.plot(df["czas_s"], df[channel], label=channel, linewidth=1.5)
    if show_limits:
        ax.axhline(0.2, color="gray", linestyle="--", linewidth=1.0, label="0.2")
        ax.axhline(0.8, color="black", linestyle="--", linewidth=1.0, label="0.8")
    ax.set_xlabel("Czas [s]")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    return fig


def main() -> None:
    st.set_page_config(page_title="RTD Analyzer COS", layout="wide")
    st.title("RTD Analyzer COS")
    st.caption("Obróbka danych RTD typu F dla modeli fizycznych COS")

    uploaded_file = st.file_uploader("Wczytaj plik CSV", type=["csv"])
    if uploaded_file is None:
        st.info("Wybierz plik CSV, aby rozpocząć analizę.")
        _render_author_footer()
        return

    try:
        raw_df = load_measurements(uploaded_file.getvalue())
    except Exception as exc:
        st.error(f"Błąd wczytania danych: {exc}")
        _render_author_footer()
        return

    channels = channel_columns(raw_df)
    st.subheader("Ustawienia")
    col1, col2, col3 = st.columns(3)
    with col1:
        discard_rows = st.number_input(
            "Ilość pomiarów do odrzucenia (wiersze od początku)",
            min_value=0,
            value=1,
            step=1,
        )
    with col2:
        start_offset = st.number_input(
            "Przesunięcie startu krzywych (dodatkowe wiersze)",
            min_value=0,
            value=0,
            step=1,
        )
    with col3:
        sample_interval_s = st.number_input(
            "Interwał pomiaru [s]",
            min_value=0.001,
            value=0.3,
            step=0.1,
            format="%.3f",
        )

    selected_channels = st.multiselect(
        "Wybierz kanały (2-6)",
        options=channels,
        default=channels[: min(4, len(channels))],
    )

    if len(selected_channels) < 2:
        st.warning("Wybierz co najmniej 2 kanały.")
        _render_author_footer()
        return

    c_infinity_mode = st.radio(
        "Sposób wyznaczania C∞",
        options=["max", "last"],
        format_func=lambda m: "Maksymalna przewodność" if m == "max" else "Przewodność końcowa",
        horizontal=True,
    )

    try:
        window_df = prepare_experiment_window(
            raw_df,
            discard_rows=int(discard_rows),
            start_offset=int(start_offset),
            sample_interval_s=float(sample_interval_s),
        )
        norm_df = normalize_dimensionless(window_df, selected_channels, c_infinity_mode)
    except Exception as exc:
        st.error(f"Błąd przetwarzania: {exc}")
        _render_author_footer()
        return

    st.subheader("Wykres 1: czas [s] - przewodność [µS/cm]")
    raw_plot_df = window_df[["czas_s", *selected_channels]].copy()
    fig_raw = _plot_curves(raw_plot_df, selected_channels, "Przewodność [µS/cm]")
    st.pyplot(fig_raw, clear_figure=True)

    if "show_limits" not in st.session_state:
        st.session_state["show_limits"] = False
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Dodaj granice 0,2 i 0,8"):
            st.session_state["show_limits"] = True
    with btn_col2:
        if st.button("Ukryj granice 0,2 i 0,8"):
            st.session_state["show_limits"] = False

    st.subheader("Wykres 2: stężenie bezwymiarowe C*")
    fig_norm = _plot_curves(
        norm_df[["czas_s", *selected_channels]],
        selected_channels,
        "C* [-]",
        show_limits=st.session_state["show_limits"],
    )
    png_buffer = io.BytesIO()
    fig_norm.savefig(png_buffer, format="png", dpi=150)
    png_buffer.seek(0)
    st.pyplot(fig_norm, clear_figure=True)

    if st.button("Odczytaj wartości strefy przejściowej"):
        transitions = compute_transition_zones(norm_df, selected_channels)
        transition_df = pd.DataFrame(
            [
                {
                    "Kanał": t.channel,
                    "t(0.2) [s]": t.t_02,
                    "t(0.8) [s]": t.t_08,
                    "Strefa przejściowa [s]": t.delta_t,
                    "Status": t.status,
                }
                for t in transitions
            ]
        )
        st.session_state["transition_df"] = transition_df

    if "transition_df" in st.session_state:
        st.subheader("Strefy przejściowe")
        st.dataframe(st.session_state["transition_df"], use_container_width=True)

    st.subheader("Zapis wyników")
    base_name = st.text_input("Nazwa plików wynikowych", value="wyniki_rtd_cos")
    st.download_button(
        "Zapisz CSV (surowe po odrzuceniu)",
        data=window_df.to_csv(index=False, sep=";", decimal=",").encode("utf-8"),
        file_name=f"{base_name}_surowe.csv",
        mime="text/csv",
    )
    st.download_button(
        "Zapisz CSV (bezwymiarowe)",
        data=norm_df.to_csv(index=False, sep=";", decimal=",").encode("utf-8"),
        file_name=f"{base_name}_bezwymiarowe.csv",
        mime="text/csv",
    )
    if "transition_df" in st.session_state:
        st.download_button(
            "Zapisz CSV (strefy przejściowe)",
            data=st.session_state["transition_df"].to_csv(index=False, sep=";", decimal=",").encode(
                "utf-8"
            ),
            file_name=f"{base_name}_strefy_przejsciowe.csv",
            mime="text/csv",
        )

    st.download_button(
        "Zapisz wykres C* (PNG)",
        data=png_buffer.getvalue(),
        file_name=f"{base_name}_wykres_Cstar.png",
        mime="image/png",
    )
    _render_author_footer()


if __name__ == "__main__":
    main()

