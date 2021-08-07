from antsalg2 import AntsAlgorithm
PROFILE = False

if __name__ == "__main__":
    demo = AntsAlgorithm()
    print(f'begin')
    if PROFILE:
        print(f'profile')
        import cProfile, pstats
        profiler = cProfile.Profile()
        profiler.enable()
        print(f'profiling begin')
        demo.run()
        print(f'profiling end')
        print(f'end')
        profiler.disable()
        stats = pstats.Stats(profiler).sort_stats('ncalls')
        stats.print_stats()

        stats = pstats.Stats(profiler).sort_stats('cumtime')
        stats.print_stats()
    else:
        demo.run()
