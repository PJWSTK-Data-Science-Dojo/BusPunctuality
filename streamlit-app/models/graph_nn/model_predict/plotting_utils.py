import plotly.graph_objects as go

# Dummy stop metadata: stop_id -> (stop_name, (lat, lon))
stop_info = {2169: ('Władysława IV', (54.39869, 18.67434)),
 208: ('Nowy Port Góreckiego', (54.40005, 18.67098)),
 2166: ('Marynarki Polskiej', (54.39837, 18.66617)),
 2164: ('Śnieżna', (54.39228, 18.65767)),
 2162: ('Polsat Plus Arena Gdańsk', (54.38726, 18.6484)),
 2160: ('Mostostal', (54.38569, 18.64461)),
 2158: ('Żaglowa - Amber Expo', (54.3824, 18.63841)),
 2156: ('Swojska', (54.37888, 18.63331)),
 2154: ('Węzeł Kliniczna', (54.37649, 18.63056)),
 2068: ('Twarda', (54.37438, 18.63111)),
 2066: ('Stocznia Północna', (54.37177, 18.63392)),
 2064: ('Stocznia SKM', (54.36458, 18.6427)),
 2062: ('Plac Solidarności', (54.36036, 18.64783)),
 2002: ('Dworzec Główny', (54.35533, 18.64546)),
 2137: ('Hucisko', (54.3519, 18.64522)),
 2139: ('Powstańców Warszawskich', (54.35114, 18.63631)),
 2141: ('Paska', (54.35007, 18.62997)),
 2143: ('Ciasna', (54.34916, 18.62439)),
 2145: ('Zakopiańska', (54.34882, 18.61862)),
 2147: ('Skrajna', (54.34909, 18.61264)),
 205: ('Siedlce ', (54.34831, 18.60648)),
 2150: ('Siedlce', (54.34835, 18.60723)),
 2148: ('Skrajna', (54.34898, 18.61283)),
 2146: ('Zakopiańska', (54.34876, 18.61883)), 2144: ('Ciasna', (54.34913, 18.62468)),
 2142: ('Paska', (54.35007, 18.63029)),
 2140: ('Powstańców Warszawskich', (54.35108, 18.63661)),
 2138: ('Hucisko', (54.35183, 18.64554)),
 2001: ('Dworzec Główny', (54.3556, 18.64567)),
 2061: ('Plac Solidarności', (54.36064, 18.64769)),
 2063: ('Stocznia SKM', (54.36421, 18.64324)),
 2065: ('Stocznia Północna', (54.37195, 18.63384)),
 2067: ('Twarda', (54.37456, 18.63132)),
 2153: ('Węzeł Kliniczna', (54.3766, 18.63074)),
 2155: ('Swojska', (54.37953, 18.63445)),
 2157: ('Żaglowa - Amber Expo', (54.38248, 18.6387)),
 2159: ('Mostostal', (54.38577, 18.64501)),
 2161: ('Polsat Plus Arena Gdańsk', (54.38736, 18.64901)),
 2163: ('Śnieżna', (54.39187, 18.65726)),
 2165: ('Marynarki Polskiej', (54.3984, 18.66632)),
 2149: ('Siedlce', (54.34817, 18.60704)),
 292: ('Zajezdnia Nowy Port (techniczny)', (54.39711, 18.67366))}

# Edges: (source_id, target_id)
edge_list_ids = [(2067, 2153), (2001, 2061), (2155, 2159), (2156, 2154), (2139, 2141), (2147, 205), (2142, 2140), (2157, 2159), (2169, 208), (2061, 2063), (2154, 2068), (2153, 2155), (2166, 2164), (2165, 292), (208, 2166), (2148, 2146), (2146, 2144), (2163, 2165), (2144, 2142), (2159, 2161), (2145, 2147), (2066, 2064), (2162, 2160), (2158, 2156), (2140, 2138), (2138, 2001), (2141, 2143), (2063, 2065), (2002, 2137), (2137, 2139), (2155, 2157), (2062, 2002), (2161, 2163), (2068, 2066), (2147, 2149), (2164, 2162), (2150, 2148), (2160, 2158), (2143, 2145), (2064, 2062), (2065, 2067)]

def plot_basic_graph(edge_list_ids, stop_id_to_name_latlon):
    # Build node data
    node_lats = []
    node_lons = []
    node_texts = []

    for stop_id, (name, (lat, lon)) in stop_id_to_name_latlon.items():
        node_lats.append(lat)
        node_lons.append(lon)
        in_going_nodes_count = sum(1 for src, dst in edge_list_ids if dst == stop_id)
        out_going_nodes_count = sum(1 for src, dst in edge_list_ids if src == stop_id)
        node_texts.append(f"{stop_id}: {name}; in: {in_going_nodes_count}, out: {out_going_nodes_count}")

    # Build edge segments as separate traces
    edge_traces = []
    for src, dst in edge_list_ids:
        lat0, lon0 = stop_id_to_name_latlon[src][1]
        lat1, lon1 = stop_id_to_name_latlon[dst][1]
        edge_traces.append(go.Scattermapbox(
            lat=[lat0, lat1],
            lon=[lon0, lon1],
            mode='lines',
            line=dict(width=2, color='gray'),
            hoverinfo='none'
        ))

    # Add node trace
    node_trace = go.Scattermapbox(
        lat=node_lats,
        lon=node_lons,
        mode='markers+text',
        marker=dict(size=10, color='skyblue'),
        text=node_texts,
        textposition='top center',
        hoverinfo='text'
    )

    # Map layout
    fig = go.Figure(edge_traces + [node_trace])
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",  # tile style (street map)
            center=dict(lat=54.365, lon=18.645),  # approximate center
            zoom=12
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        title="Bus Graph on Real Map",
        title_x=0.5
    )

    # fig.show()
    return fig

def print_graph_tree(edge_list_names):
    # Print all edges first
    print("\n--- All edges ---")
    for i, (src, dst) in enumerate(edge_list_names):
        print(f"{i}: {src} -> {dst}")

    # Optional: build adjacency list for easier traversal
    from collections import defaultdict

    adjacency = defaultdict(list)
    for src, dst in edge_list_names:
        adjacency[src].append(dst)

    # Step 3: Optional — sort neighbors alphabetically (for consistent print order)
    for src in adjacency:
        adjacency[src].sort()

    # Step 4: Choose a starting node (or all sources without incoming edges)
    # First build reverse index to find root nodes
    reverse_index = defaultdict(set)
    for src, dst in edge_list_names:
        reverse_index[dst].add(src)

    # Root nodes: nodes that only appear as sources, not as destinations
    root_nodes = [src for src in adjacency if src not in reverse_index]

    print("\n--- Structured Edge Tree ---")
    visited_edges = set()

    def dfs(node, depth=0):
        for neighbor in adjacency.get(node, []):
            edge = (node, neighbor)
            if edge not in visited_edges:
                print("  " * depth + f"{node} -> {neighbor}")
                visited_edges.add(edge)
                dfs(neighbor, depth + 1)

    # Step 5: Print from each root node
    for root in root_nodes:
        dfs(root)
# plot_basic_graph(edge_list_ids, stop_info)