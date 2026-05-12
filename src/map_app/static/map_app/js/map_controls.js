function tuneMobileSpiderfyDistance(clusterGroup) {
    if (!clusterGroup || !clusterGroup.options) return;
    if (window.innerWidth > 768) return;
    clusterGroup.options.spiderfyDistanceMultiplier = 0.95;
}
