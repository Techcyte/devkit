# Posting Results from an External Model

Some requests can trigger a 3rd party AI model to analyze scans.
That 3rd party will then be able to post the results of the analysis.
The REST endpoint where those results may be posted is documented in the [Techcyte Swagger docs](https://api.ci.techcyte.com/docs/#/External%20Results).

## Results Schema

### Request Body

| Key | Description | Type |
| --- | --- | --- |
| caseResults | Free form results for all scans in the request. Use if there are high level, cross scan results found by the model. | object |
| scanResults | Array of results for each scan in the request | array of objects (ScanResult) |

#### ScanResult object

| Key | Description | Type |
| --- | --- | --- |
| scanId | id of scan | string |
| results | Free form high level results for the scan. Use if there are high level results for the scan. | object |
| geojson | Feature collection containing annotations found on the scan | object (GeoJSON feature collection) |

The `results` object has two special keys: `external_url` and `summary`, both are required to be strings.
If `external_url` is set, then the Techcte UI will create a clickable link to the provided url when displaying the scan results.
The `summary` for each scan will be displayed at a top level alongside the scans in the ai results panel.
All other keys will be displayed when viewing algorithm details for each scan.

#### GeoJSON

Annotations reported to techcyte will use the GeoJSON standard.
For each scan the client will report a GeoJSON [`FeatureCollection`](https://datatracker.ietf.org/doc/html/rfc7946#section-3.3) that contains all the annotations reported for that scan.
Each reported annotation will be a `Feature` object within the `FeatureCollection`, and each `Feature` must have an `annotation_type` key defined in its `properties` field.

Each GeoJSON feature contains a geometry that can be a one of multiple types.
In the example there is a [`Polygon`](https://datatracker.ietf.org/doc/html/rfc7946#section-3.1.6), a [`MultiPoint`](https://datatracker.ietf.org/doc/html/rfc7946#section-3.1.3) and a [`GeometryCollection`](https://datatracker.ietf.org/doc/html/rfc7946#section-3.1.8).

Heatmaps may be reported as a set of contours in a single Feature with a geometry type of `GeometryCollection`.
The contours are `Polygon` geometries and their color is specified with the `contour_colors` key in the properties map of the `GeometryCollection`.
The `countour_colors` is an array of color hex strings.

See more information about the GeoJSON standard on the [GeoJSON format standard website](https://datatracker.ietf.org/doc/html/rfc7946).

## Example

```json
{
  "caseResults": {
    "mitosis_count": 1000
  },
  "scanResults": [
    {
      "scanId": "T1J4hvqyD4",
      "results": {
        "mitosis_count": 550,
        "ki67score": .55,
        "external_url": "https://fake.my-app.com/results/for/this/scan",
        "summary": "this is my summary"
      },
      "geojson": {
        "type": "FeatureCollection",
        "features": [
          {
            "type": "Feature",
            "bbox": [ 250, 100, 300, 200 ],
            "geometry": {
              "type": "Polygon",
              "coordinates": [
                [
                  [ 250, 100 ],
                  [ 250, 200 ],
                  [ 300, 250 ],
                  [ 300, 100 ],
                  [ 250, 100 ]
                ]
              ]
            },
            "properties": {
              "annotation_type": "tumor"
            }
          },
          {
            "type": "Feature",
            "properties": {
              "annotation_type": "tumor_confidence",
              "contour_colors": [
                "#AA0000",
                "#CC0000",
                "#FF0000"
              ]
            },
            "geometry": {
              "type": "GeometryCollection",
              "geometries": [
                {
                  "type": "Polygon",
                  "coordinates": [
                    [
                      [ 1, 2 ],
                      [ 3, 2 ],
                      [ 3, 5 ],
                      [ 1, 5 ],
                      [ 1, 2 ]
                    ]
                  ]
                },
                {
                  "type": "Polygon",
                  "coordinates": [
                    [
                      [ 1, 2 ],
                      [ 3, 2 ],
                      [ 3, 5 ],
                      [ 1, 5 ],
                      [ 1, 2 ]
                    ]
                  ]
                },
                {
                  "type": "Polygon",
                  "coordinates": [
                    [
                      [ 1, 2 ],
                      [ 3, 2 ],
                      [ 3, 5 ],
                      [ 1, 5 ],
                      [ 1, 2 ]
                    ]
                  ]
                }
              ]
            }
          }
        ]
      }
    },
    {
      "scanId": "T1J4hvqyD5",
      "results": {
        "mitosis_count": 450
      },
      "geojson": {
        "type": "FeatureCollection",
        "features": [
          {
            "type": "Feature",
            "geometry": {
              "type": "MultiPoint",
              "coordinates": [
                [ 80, 50 ],
                [ 90, 49 ],
                [ 60, 30 ]
              ]
            },
            "properties": {
              "annotation_type": "mitosis_count"
            }
          }
        ]
      }
    }
  ]
}
```
