FROM gcc:latest
WORKDIR /app
COPY . .
RUN g++ -o main_app main.cpp Thruster.cpp
CMD ["./main_app"]