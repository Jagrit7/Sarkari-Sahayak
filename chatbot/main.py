import asyncio
from src.core.transport import configure_transport
from src.core.pipeline import create_pipeline


async def main():
    room_name = "support-room"
    transport = await configure_transport(room_name)

    # 2. Build the pipeline and unpack the runner and worker
    runner, worker = await create_pipeline(transport)

    # 3. Register your pipeline worker to the runner's shared message bus
    await runner.add_workers(worker)

    # 4. Start the execution loop and keep the process alive
    print(f" Bot is booting up and joining room: {room_name}...")
    await runner.run()


if __name__ == "__main__":
    # Start the native Python asynchronous event loop
    asyncio.run(main())