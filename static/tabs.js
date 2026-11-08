// Shows only the panel of the selected .tab. The selection is kept in the
// address, so a reload or a link back to the page stays on the same panel.

const tabs = [...document.querySelectorAll(".tab")];
const panelId = (tab) => tab.getAttribute("aria-controls");

const selectTab = (selected) => {
    tabs.forEach((tab) => {
        const isSelected = tab === selected;
        tab.setAttribute("aria-selected", isSelected);
        document.getElementById(panelId(tab)).hidden = !isSelected;
    });
};

tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        selectTab(tab);
        history.replaceState(null, "", `#${panelId(tab)}`);
    });
});

const tabFromAddress = tabs.find((tab) => `#${panelId(tab)}` === location.hash);
if (tabFromAddress) {
    selectTab(tabFromAddress);
}
