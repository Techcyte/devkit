# Techcyte: Model Hosting Service

## I. Introduction

The **Model Hosting Service (MHS)** is a standalone product designed to provide GPU-based batch processing for Techcyte users. Using their existing Docker tools, users can easily upload their container image to Techcyte and configure them as custom classifiers on the Techcyte platform.

## II. Prerequisites

In order to use the ECS you'll need:

1. A Techcyte account with appropriate permission (Lab Admin or Lab User)  
2. The "Model Hosting Service" feature flag turned on

## III. Step-by-Step Instructions

We'll need to: upload your Docker image, define a runnable container type, configure a case algorithm to use the container, and run a task on your scan.

### 1: Upload your Docker image

* **Visit the Model Hosting Service page**: From your worklist view, select the Model Hosting Service from the menu dropdown  

  ![](images/image10.png)  

* **Create an image definition:** Select the "Docker Images" tab  

  ![](images/image4.png)

* **Click Create Image**  

  ![](images/image11.png)

* **Name your image and click "Create"**  

  ![](images/image9.png)

* **Upload your Docker image:** 

From the command line, in the directory containing your Dockerfile, scripts, execute the four commands shown in the "Docker Push Instructions" modal. See example template files [here](../../model-hosting-service.md).

Use the "Copy to clipboard" button for long commands. Uploading may take several minutes.  Once you've uploaded your image, the image status should say "uploaded".

  ![](images/image13.png)

  ![](images/image14.png)  

  ![](images/image3.png)

### 2: Create a runnable container

* **Visit the Runnable Containers page**.  

  ![](images/image4.png)

* **Click "Create Container"**  

  ![](images/image16.png)

* **Configure your container:** Set the name, select your image, and AWS runtime instance type. You can also configure additional environment variables to customize the container behavior. These variables are sent to the container with each invocation, along with the dynamic default pairs (listed [here](../../model-hosting-service.md#environment-variables)).  

  ![](images/image5.png)

### 3: Setup a Case algorithm for your container

From here, we'll need to configure your cases to use your newly created runnable container.

* **Visit your Company Configuration page:** From the menu dropdown select "Company settings" \-\> "Configuration"  

  ![](images/image6.png)

* **Create a new Case algorithm:** Click the \+ icon at the top right  

  ![](images/image12.png)
  

* **Configure the case algorithm:** Name your algorithm, select "Model Hosting Service" as the Model provider, and select your container.  

  ![](images/image15.png)

### 4: Run an AI Request on your scan

* **Create an AI Request:** From the case view, right click on your scanned image and select "AI Task" or "AI Request" 

  ![](images/image2.png)

  NOTE: If an "AI models" request type is not available, you'll need to create one, see [Creating an AI request type](../creating-an-ai-request-type/index.md)

* **Submit the request**: From the Create request \-\> AI Task dialog, select your Case algorithm (My GPU Container here) as the AI model and create the request  

  ![](images/image8.png)


At this point your container will start up, and begin processing the image as you have configured it.

## IV. Troubleshooting

Logs will are viewable from the "Jobs and Logs" tab on the Model Hosting Service page.  

![](images/image4.png)

![](images/image101.png)

![](images/image102.png)

## V. Conclusion

In a few steps we've uploaded a Docker image, created a runnable container type, defined a case algorithm to use the container, and run an AI task on an uploaded scan. The Model Hosting Service is in active development so new features will be added over time. Images may not be up to date.