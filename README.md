# Coat of Arms API

A simple, public JSON API containing information about various city coats of arms — including images, descriptions, mottos, and designer details.

Data is hosted on GitHub and can be fetched directly as a JSON file.

---

## API Endpoint
[json](https://raw.githubusercontent.com/stuffbymax/coats/refs/heads/main/db.json)


## examples 

### javascript

```js
// Example: Fetch and display coat of arms for a given city

async function getCoatOfArms(cityName) {
  const response = await fetch('https://raw.githubusercontent.com/stuffbymax/coats/refs/heads/main/db.json');
  const data = await response.json();

  const coat = data.coatOfArms.find(
    (item) => item.name.toLowerCase() === cityName.toLowerCase()
  );

  if (!coat) {
    console.log('No coat of arms found for that city.');
    return;
  }

  console.log(`🏙️ City: ${coat.name}`);
  console.log(`📜 Description: ${coat.description}`);
  console.log(`🎨 Designer: ${coat.designer}`);
  console.log(`🖼️ Image: ${coat.image}`);
  console.log(`💬 Motto (Latin): ${coat.motto.latin}`);
  console.log(`💬 Motto (English): ${coat.motto.english}`);
  if (coat.motto.czech) console.log(`💬 Motto (Czech): ${coat.motto.czech}`);
}

getCoatOfArms('Prague');

```
---

## Python Example

```python
import requests

def get_coat_of_arms(city_name):
    url = "https://raw.githubusercontent.com/stuffbymax/coats/refs/heads/main/db.json"
    response = requests.get(url)
    response.raise_for_status()  # Raise an error if the request fails

    data = response.json()
    coats = data.get("coatOfArms", [])

    # Find the coat of arms by city name (case-insensitive)
    for coat in coats:
        if coat["name"].lower() == city_name.lower():
            print(f"🏙️ City: {coat['name']}")
            print(f"📜 Description: {coat['description']}")
            print(f"🎨 Designer: {coat['designer']}")
            print(f"🖼️ Image: {coat['image']}")
            motto = coat.get("motto", {})
            print(f"💬 Latin: {motto.get('latin')}")
            print(f"💬 English: {motto.get('english')}")
            if motto.get("czech"):
                print(f"💬 Czech: {motto['czech']}")
            return

    print("No coat of arms found for that city.")

get_coat_of_arms("Prague")

```

---

## react 
```js
import { useState, useEffect } from "react";

function CoatOfArmsFinder() {
  const [city, setCity] = useState("");
  const [coat, setCoat] = useState(null);
  const [data, setData] = useState([]);

  // Fetch the data once on mount
  useEffect(() => {
    fetch("https://raw.githubusercontent.com/stuffbymax/coats/refs/heads/main/db.json")
      .then((res) => res.json())
      .then((json) => setData(json.coatOfArms || []))
      .catch((err) => console.error("Error fetching data:", err));
  }, []);

  const handleSearch = () => {
    const match = data.find(
      (item) => item.name.toLowerCase() === city.trim().toLowerCase()
    );
    setCoat(match || null);
  };

  return (
    <div style={{ fontFamily: "sans-serif" }}>
      <h1>Coat of Arms Finder</h1>
      <input
        type="text"
        placeholder="Enter city name"
        value={city}
        onChange={(e) => setCity(e.target.value)}
      />
      <button onClick={handleSearch}>Search</button>

      {coat ? (
        <div style={{ marginTop: "20px" }}>
          <h2>{coat.name}</h2>
          <img
            src={coat.image}
            alt={`Coat of arms of ${coat.name}`}
            style={{ maxWidth: "300px", height: "auto" }}
          />
          <p>{coat.description}</p>
          <p><strong>Latin:</strong> {coat.motto.latin}</p>
          <p><strong>English:</strong> {coat.motto.english}</p>
          {coat.motto.czech && <p><strong>Czech:</strong> {coat.motto.czech}</p>}
          <p><strong>Designer:</strong> {coat.designer}</p>
        </div>
      ) : (
        <p style={{ marginTop: "20px" }}>Enter a city name to begin.</p>
      )}
    </div>
  );
}

export default CoatOfArmsFinder;

```
