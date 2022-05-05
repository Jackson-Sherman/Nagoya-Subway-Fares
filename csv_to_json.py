import csv
import json
import heapq

INF = float('inf')

def convert(filepath):
    output = {}
    names = {}
    with open(filepath, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            letter = row[0][0]
            if letter not in output:
                output[letter] = {'dist': [], 'also': {}}
            names[row[0]] = row[1]
            output[letter]['dist'].append(int(10*float(row[2])))
            if row[3]:
                output[letter]['also'][row[0]] = row[3]

    labels = {}

    for label, station in names.items():
        if station in labels:
            labels[station].append(label)
            labels[station].sort()
        else:
            labels[station] = [label]
    
    return {"lines": output, "names": names, "labels": labels}

def add_data(new_data, path):
    with open(path, 'w') as file:
        json.dump(new_data, file, indent=4, ensure_ascii=False)

def get_intersections(data):
    pairs = set()
    for line in data['lines'].values():
        a = line["also"]
        pairs |= {frozenset({k,a[k]}) for k in a}
    output = {}
    for pair in pairs:
        output[data["names"][next(iter(pair))]] = sorted(pair)
    return output
            
def data_to_graph(data):
    lines, names = data['lines'], data['names']
    output = {}
    for letter in lines:
        line = lines[letter]
        label = lambda ind: "%s%02d" % (letter, ind+1)
        km = line['dist']
        n = len(km)
        for i in range(n):
            lab = label(i)
            station = names[lab]
            neighbors = {}
            if km[0] != 0:
                if i == 0:
                    neighbors[names[label(n-1)]] = km[0] - km[n-1]
                    neighbors[names[label(1)]] = km[1]
                elif i == 1:
                    neighbors[names[label(0)]] = km[1]
                    neighbors[names[label(2)]] = km[2] - km[1]
                elif i + 1 == n:
                    neighbors[names[label(i-1)]] = km[i] - km[i-1]
                    neighbors[names[label(0)]] = km[0] - km[i]
                else:
                    neighbors[names[label(i-1)]] = km[i] - km[i-1]
                    neighbors[names[label(i+1)]] = km[i+1] - km[i]
            else:
                if 0 < i:
                    neighbors[names[label(i-1)]] = km[i] - km[i-1]
                if i + 1 < n:
                    neighbors[names[label(i+1)]] = km[i+1] - km[i]
            if station not in output:
                output[station] = {}
            output[station].update(neighbors)
            # for st in neighbors:
            #     output[station][st] = neighbors[st]
    return output
            
def shortest_path(graph, source):
    assert isinstance(graph, dict) and isinstance(source, str)

    vertecies = frozenset(graph.keys())

    assert source in vertecies

    q = set(vertecies)

    dist = {station: INF for station in vertecies}
    prev = {station: None for station in vertecies}

    dist[source] = 0

    def find_min_key(dic):
        mink,minv = next(iter(dic.items()))
        for key,val in dic.items():
            if val < minv:
                minv = val
                mink = key
        return mink
    
    while q:
        station = find_min_key({k: v for k, v in dist.items() if k in q})
        q.remove(station)

        for adj in graph[station]: 
            if adj not in q: continue
            alt = dist[station] + graph[station][adj]
            if alt < dist[adj]:
                dist[adj] = alt
                prev[adj] = station
    
    return dist, prev

def dists_to_zones(dists):
    zone = lambda km: (km + 49) // 40
    return {station: zone(km) for station, km in dists.items()}

def zoned_lines(zones, data, language="en"):
    with open("data/line_names.json", "r") as file:
        line_names = json.load(file)[language]
    names = data['names']
    lines = data['lines']
    
    for letter in lines:
        print(f"\n{'='*32}\n\n{line_names[letter]:^32}\n")
        prev = None
        for i in range(1,1+len(lines[letter]['dist'])):
            label = letter + ('0' if i < 10 else '') + str(i)
            station = names[label]
            zone = zones[station]
            if prev is not None:
                if prev == zone: print('%6s' % '│')
                else: print('─'*5+'┼'+'─'*10)
            prev = zone
            print('%2d%5s  %s' % (zone, label, station))
    
    print(f"\n{'='*32}\n")



if __name__ == '__main__':
    data = convert('data/station_dists.csv')
    add_data(data, 'data/all_data.json')
    get_intersections(data)
    graph = data_to_graph(data)

    def get_station_count(da):
        return len(set(da["names"].values()))

    with open("data/graph.json", 'w') as file:
        json.dump(graph, file, indent=4,ensure_ascii=False)
    
    dis, pre = shortest_path(graph, "名古屋大学駅")
    
    params = dict(sort_keys=True, ensure_ascii=False, indent=4)
    
    zones = dists_to_zones(dis)

    zoned_lines(zones, data)